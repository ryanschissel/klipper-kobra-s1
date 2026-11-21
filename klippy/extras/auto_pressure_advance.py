# Automatic pressure advance calibration using a load cell
#
# This module calibrates the extruder's "pressure_advance" by watching the
# nozzle/toolhead force reported by a strain gauge load cell (the CS1237
# used on the Kobra 3 Max) while the printer performs a controlled
# acceleration/deceleration extrusion.
#
# How it works (see also auto_pressure_advance_README.md):
#
#   * Klipper implements pressure advance (PA) by adding
#         pa_position(t) = nominal_position(t) + PA * nominal_velocity(t)
#     to the extruder position (klippy/chelper/kin_extruder.c).  PA only
#     matters where the velocity *changes*, i.e. during the acceleration
#     and deceleration ramps of a move.  A move with a constant velocity
#     is completely unaffected by PA.
#
#   * Note that this fork only applies PA to moves that contain X or Y
#     motion (kinematics/extruder.py: "can_pressure_advance").  A pure
#     "G1 E..." move therefore receives *no* pressure advance at all and
#     cannot be used for the measurement.  The test move used here is
#     consequently an XY move with an extrusion component.
#
#   * Physically the filament needs a little time (the "filament travel
#     delay") to reach the melt chamber.  When the toolhead accelerates
#     the chamber is briefly starved and the nozzle pressure dips; when
#     it decelerates the chamber is briefly overfilled and the pressure
#     rises.  Pressure advance compensates exactly that delay by pushing
#     extra filament during the acceleration ramp (and pulling it back
#     during the deceleration ramp).
#
#   * The correct PA is therefore the one where the two transients
#     cancel each other and the nozzle pressure simply follows the flow
#     ramp.  The measurement therefore looks for the PA value that gives
#     the *smoothest* force trace, i.e. the smallest high frequency
#     content of the load cell signal.
#
# Copyright (C) 2026
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging
import math


# Bump this whenever the option set or the behaviour changes.  It is
# reported by AUTO_PRESSURE_ADVANCE_STATUS so that it is possible to
# confirm which version of the plugin a printer is actually running.
PLUGIN_VERSION = '1.3'


class _OptionReader:
    """Read options from a Klipper config object and record their names.

    Klipper refuses to start when a config option is not read by the
    module that owns the section ("Option 'x' is not valid in section
    'y'").  Keeping track of the option names that were used makes it
    possible to detect - and consume - options that this version of the
    plugin does not know about, for example ones left over from an older
    config block.
    """

    def __init__(self, config):
        self.config = config
        self.known = set()

    def _note(self, option):
        self.known.add(option.lower())

    def get(self, option, default=None):
        self._note(option)
        return self.config.get(option, default)

    def getfloat(self, option, default=None, **kwargs):
        self._note(option)
        return self.config.getfloat(option, default, **kwargs)

    def getint(self, option, default=None, **kwargs):
        self._note(option)
        return self.config.getint(option, default, **kwargs)

    def getboolean(self, option, default=None):
        self._note(option)
        return self.config.getboolean(option, default)


# Small statistics helpers (numpy is not available inside klippy)
def _mean(values):
    if not values:
        return 0.
    return sum(values) / float(len(values))


def _median(values):
    if not values:
        return 0.
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return .5 * (ordered[mid - 1] + ordered[mid])


def _stdev(values):
    if len(values) < 2:
        return 0.
    avg = _mean(values)
    return math.sqrt(sum((v - avg) ** 2
                         for v in values) / float(len(values) - 1))


def _mode(values, bins=25):
    """Return the most common value of a sample set.

    The force trace is mostly a flat plateau surrounded by two ramps.
    The plateau is the most frequently occurring level, so a histogram
    mode finds it much more reliably than a mean or median.
    """
    if not values:
        return 0.
    lo = min(values)
    hi = max(values)
    if hi - lo < 1e-6:
        return lo
    step = (hi - lo) / float(bins)
    counts = [0] * bins
    for v in values:
        idx = int((v - lo) / step)
        if idx >= bins:
            idx = bins - 1
        elif idx < 0:
            idx = 0
        counts[idx] += 1
    best = max(range(bins), key=lambda i: counts[i])
    low = lo + (best - 0.5) * step
    high = lo + (best + 0.5) * step
    selected = [v for v in values if low <= v <= high]
    return _median(selected) if selected else lo + best * step


class AutoPressureAdvance:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name()
        self.gcode = self.printer.lookup_object('gcode')
        self.reactor = self.printer.get_reactor()

        # Read the options through a wrapper that records which option
        # names were used (see _OptionReader).
        cfg = _OptionReader(config)

        # Load cell object providing adc/raw readings (CS1237 in this fork)
        self.sensor_name = cfg.get('sensor', 'cs1237')
        self.sensor = None

        # Extruder whose pressure advance is measured
        self.extruder_name = cfg.get('extruder', 'extruder')
        # Test position (safe in-air extrusion spot)
        self.test_x = cfg.getfloat('test_x', 210.)
        self.test_y = cfg.getfloat('test_y', 210.)
        self.test_z = cfg.getfloat('test_z', 25.)
        self.use_test_position = cfg.getboolean('use_test_position', True)

        # Temperatures
        self.extruder_temp = cfg.getfloat('extruder_temp', 220., above=0.)
        self.bed_temp = cfg.getfloat('bed_temp', 0., minval=0.)

        # Test move geometry.  "filament_speed" is the speed of the
        # filament itself (mm/s), "accel_ratio" the toolhead acceleration
        # divided by the toolhead speed (1/s) - it fixes the length of the
        # acceleration ramp, which is 1/accel_ratio seconds.
        self.filament_speed = cfg.getfloat('filament_speed', 2.5, above=0.)
        self.accel_ratio = cfg.getfloat('accel_ratio', 10., above=0.)
        self.move_speed = cfg.getfloat('move_speed', 40., above=0.)
        self.move_length = cfg.getfloat('move_length', 15., above=0.)
        self.prime_length = cfg.getfloat('prime_length', 5., minval=0.)
        self.settle_time = cfg.getfloat('settle_time', 0.7, above=0.)
        self.cycles = cfg.getint('cycles', 3, minval=1)

        # Length of the high pass filter used to extract the transients.
        # Expressed as a multiple of the acceleration ramp length.
        self.window_ratio = cfg.getfloat('window_ratio', 1.5, above=0.)

        # Pressure advance sweep
        self.pa_start = cfg.getfloat('pa_start', 0., minval=0.)
        self.pa_end = cfg.getfloat('pa_end', 0.08, minval=0.)
        self.pa_step = cfg.getfloat('pa_step', 0.01, above=0.)
        if self.pa_end <= self.pa_start:
            raise config.error(
                "Option 'pa_end' in section '%s' must be larger than "
                "'pa_start'" % (self.name,))
        self.refine_passes = cfg.getint('refine_passes', 1, minval=0,
                                       maxval=3)
        self.refine_ratio = cfg.getfloat('refine_ratio', 0.25, above=0.)

        # Load cell sampling
        self.sample_rate = cfg.getfloat('sample_rate', 100., above=1.)
        # The CS1237 needs a moment to settle after it has been enabled -
        # the first readings are wildly out of range until the amplifier
        # has settled.  These samples are discarded.
        self.sensor_settle = cfg.getfloat('sensor_settle', 0.6, minval=0.)
        self.min_response_ratio = cfg.getfloat('min_response_ratio', 5.,
                                                above=0.)
        self.require_response = cfg.getboolean('require_response', True)

        # Behaviour
        self.save_config = cfg.getboolean('save_config', False)
        self.restore_sensor_state = cfg.getboolean('restore_sensor_state',
                                                   True)
        self.suspend_runout = cfg.getboolean('suspend_runout_sensors', True)

        # Pressure advance profiles - one value per filament type.  The
        # store is a "name=value" list, e.g. "PLA=0.0213, PETG=0.0245".
        # It is written by the plugin and kept by SAVE_CONFIG.
        self.profiles = self._parse_pairs(cfg.get('profiles', ''))
        # Optional map of tool index to profile name, e.g. "0=PLA, 1=PETG".
        # When the ACE Pro changes tool the matching profile is applied.
        self.tool_profiles = self._parse_pairs(cfg.get('tool_profiles', ''),
                                               numeric=True)
        self.auto_apply_profiles = cfg.getboolean('auto_apply_profiles',
                                                   True)

        # Klipper refuses to start when a config option is not read by the
        # module that owns the section.  Consume any option this version
        # does not know about (for example one left over from an older
        # config block) so that it cannot block the printer from starting.
        self.unknown_options = []
        for option in config.get_prefix_options(''):
            if option.lower() not in cfg.known:
                self.unknown_options.append(option)
                logging.warning(
                    "auto_pressure_advance: ignoring unknown option '%s' in "
                    "section '%s'", option, self.name)
                config.get(option)

        # Runtime state
        self._samples = []
        self._last_result = None
        self._sensor_state = None
        self._runout_state = None
        self._move_dir = 1.
        self._last_tool = None
        self._suspend_apply = False

        self.printer.register_event_handler('klippy:connect', self._connect)
        self.gcode.register_command(
            'AUTO_PRESSURE_ADVANCE_CALIBRATE', self.cmd_calibrate,
            desc=self.cmd_calibrate_help)
        self.gcode.register_command(
            'AUTO_PRESSURE_ADVANCE', self.cmd_calibrate,
            desc=self.cmd_calibrate_help)
        self.gcode.register_command(
            'AUTO_PRESSURE_ADVANCE_SET', self.cmd_set, desc=self.cmd_set_help)
        self.gcode.register_command(
            'AUTO_PRESSURE_ADVANCE_APPLY', self.cmd_apply,
            desc=self.cmd_apply_help)
        self.gcode.register_command(
            'AUTO_PRESSURE_ADVANCE_PROFILES', self.cmd_profiles,
            desc=self.cmd_profiles_help)
        self.gcode.register_command(
            'AUTO_PRESSURE_ADVANCE_TEST', self.cmd_test,
            desc=self.cmd_test_help)
        self.gcode.register_command(
            'AUTO_PRESSURE_ADVANCE_STATUS', self.cmd_status,
            desc=self.cmd_status_help)

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------
    def _parse_pairs(self, text, numeric=False):
        """Parse a "name=value, name=value" list into a dict.

        Profile names are matched case insensitively, so "PLA" and "pla"
        refer to the same profile.  With numeric=True the *name* is the
        integer key and the value stays a string (used for the tool
        index -> profile name map).
        """
        result = {}
        for item in (text or '').split(','):
            item = item.strip()
            if not item or '=' not in item:
                continue
            name, value = item.split('=', 1)
            name = name.strip()
            value = value.strip()
            if not name or not value:
                continue
            if numeric:
                try:
                    result[int(name)] = value.lower()
                except ValueError:
                    logging.warning("auto_pressure_advance: ignoring "
                                    "malformed tool mapping '%s'", item)
            else:
                result[name.lower()] = value
        return result

    def _format_pairs(self, pairs):
        return ", ".join("%s=%s" % (k, v) for k, v in sorted(pairs.items()))

    def _connect(self):
        sensor = self.printer.lookup_object(self.sensor_name, None)
        if sensor is None:
            raise self.printer.config_error(
                "auto_pressure_advance: load cell object '%s' not found. "
                "Check the [auto_pressure_advance] sensor option."
                % (self.sensor_name,))
        for attr in ('add_client', 'remove_client', 'start_reporting',
                     'stop_reporting'):
            if not hasattr(sensor, attr):
                raise self.printer.config_error(
                    "auto_pressure_advance: load cell '%s' does not support "
                    "the required interface (missing '%s')"
                    % (self.sensor_name, attr))
        self.sensor = sensor
        logging.info("auto_pressure_advance: using load cell '%s'",
                     self.sensor_name)
        # Watch the ACE Pro tool index so that a different pressure
        # advance can be used for every filament type.
        if self.tool_profiles and self.auto_apply_profiles:
            self._tool_timer = self.reactor.register_timer(
                self._tool_event, self.reactor.NOW + 1.)

    def _tool_event(self, eventtime):
        """Apply the pressure advance profile of the active tool."""
        if not self._suspend_apply:
            ace = self.printer.lookup_object('ace', None)
            index = None
            if ace is not None:
                try:
                    index = ace.get_status(eventtime).get('current_index')
                except Exception:
                    index = None
            if index is not None and index != self._last_tool:
                self._last_tool = index
                profile = self.tool_profiles.get(index)
                if profile is not None and profile in self.profiles:
                    advance = float(self.profiles[profile])
                    self._set_pa(advance)
                    logging.info("auto_pressure_advance: applied profile "
                                 "'%s' (%.6f) for tool %d", profile, advance,
                                 index)
        return eventtime + 1.

    def _lookup_extruder(self):
        extruder = self.printer.lookup_object(self.extruder_name, None)
        if extruder is None:
            raise self.printer.command_error(
                "auto_pressure_advance: extruder '%s' not found"
                % (self.extruder_name,))
        return extruder

    def _pause(self, delay):
        if delay > 0.:
            self.reactor.pause(self.reactor.monotonic() + delay)

    # ------------------------------------------------------------------
    # Load cell handling
    # ------------------------------------------------------------------
    def _sample_callback(self, msg):
        raw = msg.get('raw')
        if raw is None:
            raw = msg.get('adc')
        if raw is None:
            return True
        self._samples.append((msg.get('timestamp', 0.), float(raw)))
        return True

    def _start_sampling(self):
        sensor = self.sensor
        self._sensor_state = {
            'reporting': bool(getattr(sensor, '_reporting', False)),
            'enabled': int(getattr(sensor, '_enable_count', 0) or 0) > 0,
            'rate': getattr(sensor, '_samples_per_second', None),
        }
        if self._sensor_state['reporting']:
            sensor.stop_reporting()
        # Temporarily raise the MCU report rate - the default (10Hz) is far
        # too slow to resolve the acceleration ramp.
        try:
            sensor._samples_per_second = int(round(self.sample_rate))
        except Exception:
            logging.exception("auto_pressure_advance: unable to set the "
                              "load cell report rate")
        sensor.add_client(self._sample_callback)
        # The MCU only samples the ADC while the sensor is enabled
        enable = getattr(sensor, '_enable_cs1237', None)
        if enable is not None:
            enable(1)
        # The CS1237 output swings wildly for a short time after it has
        # been enabled (the amplifier needs to settle).  Wait for that and
        # throw the samples away, otherwise they poison the baseline.
        if self.sensor_settle > 0.:
            self._pause(self.sensor_settle)
        self._samples = []

    def _stop_sampling(self):
        sensor = self.sensor
        state = self._sensor_state or {}
        try:
            sensor.remove_client(self._sample_callback)
        except Exception:
            logging.exception("auto_pressure_advance: unable to remove the "
                              "load cell client")
        if state.get('rate') is not None:
            try:
                sensor._samples_per_second = state['rate']
            except Exception:
                pass
        if getattr(sensor, '_reporting', False):
            # Reporting is still wanted - restart it so that the original
            # report rate is used again
            sensor.stop_reporting()
            sensor.start_reporting()
        elif state.get('reporting'):
            sensor.start_reporting()
        if not state.get('enabled'):
            enable = getattr(sensor, '_enable_cs1237', None)
            if enable is not None:
                enable(0)
        self._sensor_state = None

    # ------------------------------------------------------------------
    # Runout / ACE monitoring suspension
    # ------------------------------------------------------------------
    def _suspend_runout_sensors(self):
        # A list of (callable, value) pairs used to restore the state
        restore = []
        for name, obj in self.printer.lookup_objects():
            helper = getattr(obj, 'runout_helper', None)
            if helper is None:
                continue
            if not hasattr(helper, 'sensor_enabled'):
                continue
            restore.append((_setter(helper, 'sensor_enabled'),
                             helper.sensor_enabled))
            helper.sensor_enabled = False
        # ACE Pro runout / tangle monitoring
        ace = self.printer.lookup_object('ace', None)
        if ace is not None:
            monitor = getattr(ace, 'runout_monitor', None)
            if monitor is not None:
                restore.append((_setter(monitor, 'runout_detection_active'),
                                getattr(monitor, 'runout_detection_active',
                                        None)))
                restore.append((_setter(monitor, 'tangle_detection_enabled'),
                                getattr(monitor, 'tangle_detection_enabled',
                                        None)))
                try:
                    ace.set_runout_detection_active(False)
                except Exception:
                    logging.exception("auto_pressure_advance: unable to "
                                      "disable ACE runout detection")
                try:
                    monitor.set_tangle_detection_enabled(False)
                except Exception:
                    logging.exception("auto_pressure_advance: unable to "
                                      "disable ACE tangle detection")
        self._runout_state = restore

    def _restore_runout_sensors(self):
        if not self._runout_state:
            return
        for setter, value in self._runout_state:
            if value is None:
                continue
            try:
                setter(value)
            except Exception:
                logging.exception("auto_pressure_advance: unable to restore "
                                  "a runout sensor state")
        self._runout_state = None

    # ------------------------------------------------------------------
    # Pressure advance handling
    # ------------------------------------------------------------------
    def _get_pa(self):
        extruder = self._lookup_extruder()
        stepper = getattr(extruder, 'extruder_stepper', None)
        if stepper is None:
            return 0.
        return float(getattr(stepper, 'pressure_advance', 0.) or 0.)

    def _set_pa(self, pa):
        self.gcode.run_script_from_command(
            "SET_PRESSURE_ADVANCE EXTRUDER=%s ADVANCE=%.6f"
            % (self.extruder_name, pa))

    # ------------------------------------------------------------------
    # Test move
    # ------------------------------------------------------------------
    def _move_command(self):
        # The move must contain X or Y motion - Klipper only applies
        # pressure advance to moves that move the toolhead.  The extrusion
        # amount is derived from the requested filament speed:
        #   e_velocity = (de / move_length) * move_speed
        de = self.filament_speed * self.move_length / self.move_speed
        dx = self._move_dir * self.move_length
        self._move_dir = -self._move_dir
        return "G1 X%.4f E%.4f F%.1f" % (dx, de, self.move_speed * 60.)

    def _set_velocity_limits(self):
        toolhead = self.printer.lookup_object('toolhead')
        old = (toolhead.max_velocity, toolhead.max_accel,
               toolhead.square_corner_velocity, toolhead.min_cruise_ratio)
        accel = self.move_speed * self.accel_ratio
        self.gcode.run_script_from_command(
            "SET_VELOCITY_LIMIT VELOCITY=%.3f ACCEL=%.3f"
            % (self.move_speed, accel))
        return old

    def _restore_velocity_limits(self, old):
        if not old:
            return
        toolhead = self.printer.lookup_object('toolhead')
        toolhead.set_max_velocities(old[0], old[1], old[2], old[3])

    def _run_test_move(self):
        """Run a single calibration move and return the collected samples.

        Returns (n_base, samples) where the first n_base samples are
        taken while the toolhead is idle and samples covers the whole
        move.
        """
        toolhead = self.printer.lookup_object('toolhead')
        # Make sure the move starts from a full stop (no junction speed)
        toolhead.flush_step_generation()
        self._samples = []
        self._pause(self.settle_time)
        n_base = len(self._samples)
        cmd = self._move_command()
        self.gcode.run_script_from_command(cmd)
        toolhead.wait_moves()
        self._pause(self.settle_time)
        return n_base, list(self._samples)

    # ------------------------------------------------------------------
    # Trace analysis
    # ------------------------------------------------------------------
    def _filter_half(self):
        """Half width of the high pass filter, in samples."""
        w = max(3, int(round(self.sample_rate / self.accel_ratio
                              * self.window_ratio)) | 1)
        return w // 2

    def _highpass(self, values):
        """Remove the slow part of the trace with a moving average."""
        half = self._filter_half()
        out = []
        total = len(values)
        for i in range(total):
            lo = i - half
            hi = i + half + 1
            if lo < 0:
                lo = 0
            if hi > total:
                hi = total
            out.append(values[i] - _mean(values[lo:hi]))
        return out

    def _rms(self, values):
        if not values:
            return 0.
        return math.sqrt(sum(v * v for v in values) / float(len(values)))

    def _analyze(self, n_base, samples):
        if len(samples) < 10 or n_base < 5:
            return None
        base_vals = [s[1] for s in samples[:n_base]]
        f_base = _mean(base_vals)
        sigma = _stdev(base_vals)
        trace = [s[1] - f_base for s in samples]
        thr = max(self.min_response_ratio * sigma, 1.)
        # Locate the move: the force leaves the idle level while the
        # filament is being extruded.
        active = [i for i, v in enumerate(trace) if abs(v) > thr]
        if len(active) < 6:
            return None
        i0, i1 = active[0], active[-1]
        plateau = _mode(trace[i0:i1 + 1])
        response = abs(plateau)
        if response < thr:
            return None
        # The score: the high frequency content of the force trace.  It is
        # minimal when the pressure advance transient cancels the transient
        # caused by the filament travel delay.
        hp = self._highpass(trace)
        # The very first and last samples of the trace are skipped: the
        # moving average is truncated there and produces a residual that
        # is not part of the measurement.
        half = self._filter_half()
        edge = min(half, max(0, (len(hp) - 1) // 2))
        core = hp[edge:len(hp) - edge] if len(hp) - 2 * edge > 0 else hp
        score = self._rms(core)
        # The noise floor: the same measure taken over the idle part of the
        # trace.  Comparing the two shows how much of the score is real
        # signal and how much is just sensor noise.
        n_edge = min(half, max(0, (n_base - 1) // 2))
        hp_base = hp[n_edge:n_base - n_edge] if n_base - 2 * n_edge > 0 \
            else hp[:n_base]
        noise = self._rms(hp_base)
        # Diagnostic: the antisymmetric part of the trace.  A positive
        # value means the start of the move deviates more than the end.
        half = (i1 - i0 + 1) // 2
        if half >= 2:
            a_start = _mean(trace[i0:i0 + half]) - plateau
            a_end = _mean(trace[i1 - half + 1:i1 + 1]) - plateau
            asym = a_start - a_end
        else:
            asym = 0.
        return {
            'score': score,
            'noise': noise,
            'signal': math.sqrt(max(0., score * score - noise * noise)),
            'asym': asym,
            'plateau': plateau,
            'response': response,
            'sigma': sigma,
            'samples': len(trace),
            'start_idx': i0,
            'end_idx': i1,
        }

    def _measure(self, pa):
        """Measure the force trace quality for one pressure advance."""
        self._set_pa(pa)
        # Give the toolhead a moment so the new PA value is in effect
        self._pause(0.2)
        scores = []
        responses = []
        asyms = []
        noises = []
        sigmas = []
        for _ in range(self.cycles):
            n_base, samples = self._run_test_move()
            res = self._analyze(n_base, samples)
            if res is None:
                continue
            scores.append(res['score'])
            responses.append(res['response'])
            asyms.append(res['asym'])
            noises.append(res['noise'])
            sigmas.append(res['sigma'])
        if not scores:
            return None
        return {
            'pa': pa,
            'score': _mean(scores),
            'response': _mean(responses),
            'asym': _mean(asyms),
            'noise': _mean(noises),
            'sigma': _mean(sigmas),
            'count': len(scores),
        }

    # ------------------------------------------------------------------
    # Sweep
    # ------------------------------------------------------------------
    def _pa_values(self, start, end, step):
        values = []
        pa = start
        while pa <= end + 1e-9:
            values.append(round(pa, 6))
            pa += step
        if not values or abs(values[-1] - end) > 1e-9:
            values.append(round(end, 6))
        return values

    def _find_best(self, results):
        """Return the pressure advance with the smoothest force trace.

        The score is minimal at the correct pressure advance.  A parabola
        is fitted through the three points around the minimum to get a
        finer estimate than the grid resolution.
        """
        results = sorted(results, key=lambda r: r['pa'])
        idx = min(range(len(results)), key=lambda i: results[i]['score'])
        best = results[idx]['pa']
        if 0 < idx < len(results) - 1:
            x0 = results[idx - 1]
            x1 = results[idx]
            x2 = results[idx + 1]
            try:
                d01 = (x1['score'] - x0['score']) / (x1['pa'] - x0['pa'])
                d12 = (x2['score'] - x1['score']) / (x2['pa'] - x1['pa'])
                a = (d12 - d01) / (x2['pa'] - x0['pa'])
                if a > 0.:
                    # y = y1 + d12*(x-x1) + a*(x-x1)*(x-x2)
                    vertex = 0.5 * (x1['pa'] + x2['pa']) - d12 / (2. * a)
                    best = min(max(vertex, x0['pa']), x2['pa'])
            except ZeroDivisionError:
                pass
        return best

    def _fit_slope(self, results):
        """Least squares slope of the score versus PA (roughness trend)."""
        if len(results) < 3:
            return 0.
        xs = [r['pa'] for r in results]
        ys = [r['score'] for r in results]
        mx, my = _mean(xs), _mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        den = sum((x - mx) ** 2 for x in xs)
        if den == 0.:
            return 0.
        return num / den

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------
    cmd_calibrate_help = (
        "Calibrate pressure advance from the load cell. Parameters: "
        "PA_START=<f> PA_END=<f> PA_STEP=<f> EXTRUDER_TEMP=<c> "
        "BED_TEMP=<c> CYCLES=<n> SAMPLE_RATE=<hz> SAVE=<0|1>")
    cmd_set_help = (
        "Set the pressure advance value. Parameters: ADVANCE=<f> "
        "SMOOTH_TIME=<s> SAVE=<0|1>")
    cmd_apply_help = (
        "Apply a stored pressure advance profile. Parameters: PROFILE=<name>")
    cmd_profiles_help = (
        "List the stored pressure advance profiles and the tool mapping.")
    cmd_test_help = (
        "Run a single calibration move and report the measured force "
        "response (diagnostics). Parameters: EXTRUDER_TEMP=<c>")
    cmd_status_help = "Report the last pressure advance calibration result."

    def cmd_profiles(self, gcmd):
        gcmd.respond_info(
            "auto_pressure_advance profiles:\n"
            "  stored  : %s\n"
            "  tools   : %s\n"
            "  current : %s"
            % (self._format_pairs(self.profiles) or "none",
               self._format_pairs(self.tool_profiles) or "none",
               "%.6f" % (self._get_pa(),)))

    def cmd_apply(self, gcmd):
        name = gcmd.get('PROFILE', None)
        if not name:
            raise gcmd.error("auto_pressure_advance: PROFILE=<name> is "
                             "required")
        key = name.strip().lower()
        if key not in self.profiles:
            raise gcmd.error(
                "auto_pressure_advance: unknown profile '%s' (known: %s)"
                % (name, ", ".join(sorted(self.profiles)) or "none"))
        advance = float(self.profiles[key])
        self._set_pa(advance)
        gcmd.respond_info("Applied pressure advance profile '%s' (%.6f)"
                          % (name, advance))

    def cmd_set(self, gcmd):
        advance = gcmd.get_float('ADVANCE', None, minval=0.)
        if advance is None:
            advance = self._get_pa()
        smooth_time = gcmd.get_float(
            'SMOOTH_TIME', None, minval=0., maxval=.200)
        extruder = gcmd.get('EXTRUDER', self.extruder_name)
        save = gcmd.get_int('SAVE', 1 if self.save_config else 0, minval=0,
                            maxval=1)
        cmd = "SET_PRESSURE_ADVANCE EXTRUDER=%s ADVANCE=%.6f" % (extruder,
                                                                  advance)
        if smooth_time is not None:
            cmd += " SMOOTH_TIME=%.4f" % (smooth_time,)
        self.gcode.run_script_from_command(cmd)
        gcmd.respond_info("Pressure advance set to %.6f" % (advance,))
        if save:
            configfile = self.printer.lookup_object('configfile')
            configfile.set(extruder, 'pressure_advance', "%.6f" % (advance,))
            gcmd.respond_info(
                "The SAVE_CONFIG command will update the printer config "
                "file with the above and restart the printer.")

    def cmd_status(self, gcmd):
        gcmd.respond_info(
            "auto_pressure_advance plugin version %s\n"
            "  sensor          : %s\n"
            "  extruder        : %s\n"
            "  unknown options : %s"
            % (PLUGIN_VERSION, self.sensor_name, self.extruder_name,
               ", ".join(self.unknown_options) or "none"))
        if not self._last_result:
            gcmd.respond_info("No pressure advance calibration has been run "
                              "yet.")
            return
        gcmd.respond_info(self._format_result(self._last_result))

    def get_status(self, eventtime=None):
        try:
            pa = self._get_pa()
        except Exception:
            pa = None
        return {
            'version': PLUGIN_VERSION,
            'sensor': self.sensor_name,
            'extruder': self.extruder_name,
            'pressure_advance': pa,
            'unknown_options': list(self.unknown_options),
        }

    def cmd_test(self, gcmd):
        # An unexpected error in this plugin must not take the printer
        # down: Klipper turns an unhandled exception in a command handler
        # into a shutdown.  Report it as a command error instead.
        try:
            self._cmd_test(gcmd)
        except gcmd.error:
            raise
        except Exception as e:
            logging.exception("auto_pressure_advance: test move failed")
            raise gcmd.error("auto_pressure_advance: internal error during "
                             "the test move: %s" % (e,))

    def _cmd_test(self, gcmd):
        extruder_temp = gcmd.get_float('EXTRUDER_TEMP', self.extruder_temp,
                                       above=0.)
        self._ensure_ready(gcmd, extruder_temp)
        old_limits = self._set_velocity_limits()
        try:
            self._start_sampling()
            n_base, samples = self._run_test_move()
            res = self._analyze(n_base, samples)
        finally:
            self._stop_sampling()
            self._restore_velocity_limits(old_limits)
        if res is None:
            raise gcmd.error(
                "auto_pressure_advance: could not measure a force response. "
                "Is the load cell reacting to extrusion?")
        gcmd.respond_info(
            "auto_pressure_advance test move (plugin version %s):\n"
            "  pressure advance : %.6f\n"
            "  force response   : %.1f counts (noise %.1f counts)\n"
            "  transient score  : %.1f counts\n"
            "  start/end asym.  : %.1f counts\n"
            "  trace samples    : %d"
            % (PLUGIN_VERSION, self._get_pa(), res['response'], res['sigma'],
               res['score'], res['asym'], res['samples']))

    def cmd_calibrate(self, gcmd):
        # An unexpected error in this plugin must not take the printer
        # down: Klipper turns an unhandled exception in a command handler
        # into a shutdown.  Report it as a command error instead.
        try:
            self._cmd_calibrate(gcmd)
        except gcmd.error:
            raise
        except Exception as e:
            logging.exception("auto_pressure_advance: calibration failed")
            raise gcmd.error("auto_pressure_advance: internal error during "
                             "the calibration: %s" % (e,))

    def _cmd_calibrate(self, gcmd):
        extruder_temp = gcmd.get_float('EXTRUDER_TEMP', self.extruder_temp,
                                       above=0.)
        bed_temp = gcmd.get_float('BED_TEMP', self.bed_temp, minval=0.)
        pa_start = gcmd.get_float('PA_START', self.pa_start, minval=0.)
        pa_end = gcmd.get_float('PA_END', self.pa_end, minval=0.)
        pa_step = gcmd.get_float('PA_STEP', self.pa_step, above=0.)
        cycles = gcmd.get_int('CYCLES', self.cycles, minval=1)
        sample_rate = gcmd.get_float('SAMPLE_RATE', self.sample_rate,
                                     above=1.)
        save = gcmd.get_int('SAVE', 1 if self.save_config else 0, minval=0,
                            maxval=1)
        extruder = gcmd.get('EXTRUDER', self.extruder_name)
        profile = gcmd.get('PROFILE', None)

        if pa_end <= pa_start:
            raise gcmd.error("auto_pressure_advance: PA_END must be larger "
                             "than PA_START")
        if pa_step <= 0.:
            raise gcmd.error("auto_pressure_advance: PA_STEP must be > 0")

        old_cycles = self.cycles
        old_rate = self.sample_rate
        old_extruder_name = self.extruder_name
        self.cycles = cycles
        self.sample_rate = sample_rate
        self.extruder_name = extruder

        try:
            self._ensure_ready(gcmd, extruder_temp, bed_temp)
            result = self._run_calibration(gcmd, pa_start, pa_end, pa_step)
        finally:
            self.cycles = old_cycles
            self.sample_rate = old_rate
            self.extruder_name = old_extruder_name

        if result is None:
            raise gcmd.error("auto_pressure_advance: calibration failed")

        best_pa = result['pa']
        gcmd.respond_info(self._format_result(result))
        if result.get('edge'):
            gcmd.respond_info(
                "WARNING: the best pressure advance is at the edge of the "
                "tested range.  Widen PA_START/PA_END and run again.")
        if result.get('spread', 0.) < result.get('noise', 0.):
            gcmd.respond_info(
                "WARNING: the difference between the best and the worst "
                "measured pressure advance is smaller than the sensor noise "
                "floor.  The result is not reliable - try more cycles, a "
                "slower test move or a hotter nozzle.")
        if save:
            configfile = self.printer.lookup_object('configfile')
            configfile.set(extruder, 'pressure_advance', "%.6f" % (best_pa,))
            gcmd.respond_info(
                "The SAVE_CONFIG command will update the printer config "
                "file with the above and restart the printer.")
        if profile:
            # Store the result under a name so that it can be selected per
            # filament type later on.
            key = profile.strip().lower()
            self.profiles[key] = "%.6f" % (best_pa,)
            configfile = self.printer.lookup_object('configfile')
            configfile.set(self.name, 'profiles', self._format_pairs(
                self.profiles))
            gcmd.respond_info(
                "Stored pressure advance profile '%s' = %.6f.  Run "
                "SAVE_CONFIG to keep it." % (profile, best_pa))

    def _format_result(self, result):
        lines = ["auto_pressure_advance result:",
                 "  pressure advance : %.6f" % (result['pa'],),
                 "  force response   : %.1f counts" % (result.get('response',
                                                                   0.),),
                 "  noise floor      : %.1f counts" % (result.get('noise', 0.),),
                 "  score spread     : %.1f counts" % (result.get('spread',
                                                                   0.),),
                 "  score trend      : %.1f counts per PA unit"
                 % (result.get('slope', 0.),),
                 "  sweep (lower score = smoother force trace):"]
        for entry in result.get('sweep', []):
            lines.append("    pa=%.4f score=%9.1f response=%9.1f asym=%9.1f"
                         % (entry['pa'], entry['score'], entry['response'],
                            entry['asym']))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Calibration driver
    # ------------------------------------------------------------------
    def _ensure_ready(self, gcmd, extruder_temp, bed_temp=0.):
        toolhead = self.printer.lookup_object('toolhead')
        curtime = self.reactor.monotonic()
        homed = toolhead.get_status(curtime).get('homed_axes', '')
        missing = [a for a in 'xyz' if a not in homed]
        if missing:
            raise gcmd.error(
                "auto_pressure_advance: axis %s must be homed before "
                "calibration (run G28)" % (",".join(missing),))
        print_stats = self.printer.lookup_object('print_stats', None)
        if print_stats is not None:
            state = print_stats.get_status(curtime).get('state', '')
            if state in ('printing', 'paused'):
                raise gcmd.error(
                    "auto_pressure_advance: cannot calibrate while the "
                    "printer is %s" % (state,))
        if bed_temp > 0.:
            self.gcode.run_script_from_command("M140 S%.0f" % (bed_temp,))
        self.gcode.run_script_from_command("M104 S%.0f" % (extruder_temp,))
        self.gcode.run_script_from_command("M109 S%.0f" % (extruder_temp,))
        extruder = self._lookup_extruder()
        if not extruder.get_status(curtime).get('can_extrude', True):
            raise gcmd.error(
                "auto_pressure_advance: the extruder is not ready to extrude "
                "(nozzle temperature or heater problem)")
        if self.use_test_position:
            self.gcode.run_script_from_command(
                "G90\nG1 X%.3f Y%.3f Z%.3f F6000"
                % (self.test_x, self.test_y, self.test_z))
            self.printer.lookup_object('toolhead').wait_moves()

    def _run_calibration(self, gcmd, pa_start, pa_end, pa_step):
        old_limits = self._set_velocity_limits()
        if self.suspend_runout:
            self._suspend_runout_sensors()
        # Do not let the automatic profile application interfere with the
        # measurement (it would change the pressure advance mid sweep).
        self._suspend_apply = True
        try:
            self._start_sampling()
            # Prime the extruder so the nozzle is purged and the melt
            # chamber is in a steady state.
            if self.prime_length > 0.:
                self.gcode.run_script_from_command(
                    "G1 E%.3f F%.0f" % (self.prime_length,
                                        self.filament_speed * 60.))
                self.printer.lookup_object('toolhead').wait_moves()
                self._pause(self.settle_time)

            # Response check - make sure the load cell reacts at all
            check = self._measure(pa_start)
            if check is None:
                raise gcmd.error(
                    "auto_pressure_advance: the load cell did not show a "
                    "usable force response while extruding.  Check that the "
                    "strain gauge is mounted in the filament/extruder path "
                    "and that the nozzle is hot.")
            if check['response'] < self.min_response_ratio * check['sigma']:
                msg = ("auto_pressure_advance: the load cell response to "
                       "extrusion is very small (%.1f counts vs %.1f counts "
                       "of noise).  The result will be unreliable."
                       % (check['response'], check['sigma']))
                if self.require_response:
                    raise gcmd.error(msg)
                gcmd.respond_info("WARNING: " + msg)

            sweep = []
            results = []
            pa_values = self._pa_values(pa_start, pa_end, pa_step)
            gcmd.respond_info(
                "auto_pressure_advance: sweeping pressure advance "
                "%.3f..%.3f in %.3f steps (%d points, %d cycles each)"
                % (pa_start, pa_end, pa_step, len(pa_values), self.cycles))
            for pa in pa_values:
                res = self._measure(pa)
                if res is None:
                    gcmd.respond_info("  pa=%.4f  no usable measurement"
                                      % (pa,))
                    continue
                sweep.append(res)
                results.append(res)
                gcmd.respond_info("  pa=%.4f score=%9.1f response=%9.1f "
                                  "asym=%9.1f"
                                  % (res['pa'], res['score'], res['response'],
                                     res['asym']))
            if len(results) < 3:
                raise gcmd.error(
                    "auto_pressure_advance: not enough usable measurements "
                    "to calibrate pressure advance")

            best_pa = self._find_best(results)

            # Refinement passes around the current best value
            for pas in range(self.refine_passes):
                step = pa_step * (self.refine_ratio ** (pas + 1))
                lo = max(pa_start, best_pa - pa_step)
                hi = min(pa_end, best_pa + pa_step)
                if hi - lo < step:
                    break
                fine = []
                for pa in self._pa_values(lo, hi, step):
                    res = self._measure(pa)
                    if res is None:
                        continue
                    fine.append(res)
                    gcmd.respond_info("  pa=%.4f score=%9.1f response=%9.1f"
                                      % (res['pa'], res['score'],
                                         res['response']))
                if len(fine) < 3:
                    break
                sweep.extend(fine)
                results = fine
                best_pa = self._find_best(fine)

            slope = self._fit_slope(results)
            edge = (best_pa <= pa_start + 1e-9 or best_pa >= pa_end - 1e-9)
            noise = _mean([r.get('noise', 0.) for r in results])
            spread = (max(r['score'] for r in results)
                      - min(r['score'] for r in results))
            self._last_result = {
                'pa': best_pa,
                'edge': edge,
                'slope': slope,
                'noise': noise,
                'spread': spread,
                'response': _mean([r['response'] for r in results]),
                'sweep': sweep,
            }
            # Apply the result
            self._set_pa(best_pa)
            return self._last_result
        finally:
            self._suspend_apply = False
            self._stop_sampling()
            self._restore_velocity_limits(old_limits)
            if self.suspend_runout:
                self._restore_runout_sensors()


def _setter(obj, attr):
    """Return a callable that restores obj.attr to a given value."""
    def _restore(value):
        setattr(obj, attr, value)
    return _restore


def load_config(config):
    return AutoPressureAdvance(config)
