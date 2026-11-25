# Automatic pressure advance calibration using the CS1237 load cell.
#
# Runs a sequence of extrusion moves at different pressure_advance values while
# sampling CS1237 force/ADC data, then selects the value that minimizes nozzle
# force variation during speed transitions.
#
# Designed for Kobra 3 Max / custom Klipper fork with [cs1237] and probe_ks1.
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging
import math


class AutoPressureAdvance:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.reactor = self.printer.get_reactor()
        self.name = config.get_name()

        # Test position (must be safe for in-air extrusion)
        self.test_x = config.getfloat('test_x', 210.0)
        self.test_y = config.getfloat('test_y', 210.0)
        self.test_z = config.getfloat('test_z', 50.0, above=5.0)

        # Temperature defaults
        self.extruder_temp = config.getfloat('extruder_temp', 220.0, above=0.)
        self.bed_temp = config.getfloat('bed_temp', None)

        # PA sweep
        self.pa_start = config.getfloat('pa_start', 0.0, minval=0.0)
        self.pa_end = config.getfloat('pa_end', 0.10, minval=0.0)
        self.pa_step = config.getfloat('pa_step', 0.01, above=0.0005)

        # Extrusion test profile
        self.extrude_length = config.getfloat('extrude_length', 30.0, above=1.0)
        self.speed_slow = config.getfloat('speed_slow', 3.0, above=0.5)
        self.speed_fast = config.getfloat('speed_fast', 15.0, above=1.0)
        self.slow_ratio = config.getfloat('slow_ratio', 0.25, minval=0.1,
                                          maxval=0.45)
        self.retract_length = config.getfloat('retract_length', 2.0, minval=0.)
        self.retract_speed = config.getfloat('retract_speed', 30.0, above=1.)
        self.prime_length = config.getfloat('prime_length', 2.0, minval=0.)
        self.settle_time = config.getfloat('settle_time', 0.5, minval=0.)
        self.cycles = config.getint('cycles', 2, minval=1, maxval=10)

        # CS1237 sampling
        self.sample_period = config.getfloat('sample_period', 0.1, minval=0.02,
                                             maxval=1.0)
        self.sensor_name = config.get('sensor', 'cs1237')
        self.save_config = config.getboolean('save_config', False)

        self.gcode.register_command(
            'AUTO_PRESSURE_ADVANCE_CALIBRATE',
            self.cmd_AUTO_PRESSURE_ADVANCE_CALIBRATE,
            desc=self.cmd_AUTO_PRESSURE_ADVANCE_CALIBRATE_help)
        self.gcode.register_command(
            'AUTO_PRESSURE_ADVANCE',
            self.cmd_AUTO_PRESSURE_ADVANCE_CALIBRATE,
            desc=self.cmd_AUTO_PRESSURE_ADVANCE_CALIBRATE_help)
        self.gcode.register_command(
            'AUTO_PRESSURE_ADVANCE_SET',
            self.cmd_AUTO_PRESSURE_ADVANCE_SET,
            desc=self.cmd_AUTO_PRESSURE_ADVANCE_SET_help)

    cmd_AUTO_PRESSURE_ADVANCE_CALIBRATE_help = (
        "Calibrate pressure advance using CS1237 load cell. "
        "Params: PA_START= PA_END= PA_STEP= EXTRUDER_TEMP= BED_TEMP= "
        "EXTRUDE_LENGTH= SPEED_SLOW= SPEED_FAST= CYCLES= SAVE=")
    cmd_AUTO_PRESSURE_ADVANCE_SET_help = (
        "Set pressure advance. Params: ADVANCE= SMOOTH_TIME= EXTRUDER= SAVE=")

    # ---- utilities ----
    def _script(self, cmd):
        self.gcode.run_script_from_command(cmd)

    def _get_extruder_name(self, gcmd):
        name = gcmd.get('EXTRUDER', None)
        if name:
            if not name.startswith('extruder'):
                name = 'extruder' + name
            return name
        toolhead = self.printer.lookup_object('toolhead')
        extruder = toolhead.get_extruder()
        return extruder.get_name()

    def _set_pa(self, extruder_name, pa, smooth_time=None):
        cmd = "SET_PRESSURE_ADVANCE EXTRUDER=%s ADVANCE=%.6f" % (
            extruder_name, pa)
        if smooth_time is not None:
            cmd += " SMOOTH_TIME=%.6f" % (smooth_time,)
        self._script(cmd)

    def _save_pa(self, extruder_name, pa, smooth_time=None):
        configfile = self.printer.lookup_object('configfile')
        configfile.set(extruder_name, 'pressure_advance', "%.6f" % (pa,))
        if smooth_time is not None:
            configfile.set(extruder_name, 'pressure_advance_smooth_time',
                           "%.6f" % (smooth_time,))

    def _ensure_homed(self, gcmd):
        toolhead = self.printer.lookup_object('toolhead')
        curtime = self.reactor.monotonic()
        homed = toolhead.get_status(curtime).get('homed_axes', '')
        if 'x' not in homed or 'y' not in homed or 'z' not in homed:
            raise gcmd.error(
                "AUTO_PRESSURE_ADVANCE: printer must be homed (X, Y, Z)")

    def _lookup_cs1237(self, gcmd):
        sensor = self.printer.lookup_object(self.sensor_name, None)
        if sensor is None:
            raise gcmd.error(
                "AUTO_PRESSURE_ADVANCE: sensor '%s' not found (CS1237 required)"
                % (self.sensor_name,))
        return sensor

    def _pause(self, seconds):
        if seconds and seconds > 0:
            self.reactor.pause(self.reactor.monotonic() + seconds)

    # ---- CS1237 sampling ----
    class _SampleCollector:
        def __init__(self):
            self.samples = []

        def cb(self, msg):
            if msg is None:
                return True
            ts = msg.get('timestamp', 0.0)
            adc = msg.get('adc', msg.get('raw', 0))
            raw = msg.get('raw', adc)
            state = msg.get('state', 0)
            self.samples.append((float(ts), float(adc), float(raw), int(state)))
            return True

        def clear(self):
            self.samples = []

    def _enable_sensor_reporting(self, sensor):
        # Best-effort enable/report for CS1237 custom API
        try:
            if hasattr(sensor, '_enable_count'):
                if sensor._enable_count == 0 and hasattr(sensor, '_enable_cs1237'):
                    sensor._enable_cs1237(1)
                sensor._enable_count += 1
        except Exception:
            logging.exception("AUTO_PRESSURE_ADVANCE: sensor enable failed")
        try:
            if hasattr(sensor, '_samples_per_second'):
                sensor._samples_per_second = max(
                    1, int(round(1.0 / self.sample_period)))
        except Exception:
            pass
        try:
            if hasattr(sensor, 'start_reporting'):
                sensor.start_reporting()
            if hasattr(sensor, '_check_start'):
                sens = getattr(sensor, 'sensitivity', -2000)
                sensor._check_start(self.sample_period, 1, sens, 0)
        except Exception:
            logging.exception("AUTO_PRESSURE_ADVANCE: sensor reporting start failed")

    def _disable_sensor_reporting(self, sensor):
        try:
            if hasattr(sensor, '_check_stop'):
                sensor._check_stop(1)
        except Exception:
            pass
        try:
            if hasattr(sensor, 'stop_reporting'):
                sensor.stop_reporting()
        except Exception:
            pass
        try:
            if hasattr(sensor, '_enable_count'):
                sensor._enable_count -= 1
                if sensor._enable_count <= 0:
                    sensor._enable_count = 0
                    if hasattr(sensor, '_enable_cs1237'):
                        sensor._enable_cs1237(0)
        except Exception:
            logging.exception("AUTO_PRESSURE_ADVANCE: sensor disable failed")

    # ---- metrics ----
    def _score_samples(self, samples, baseline):
        # Use adc values; lower score is better (more stable pressure/force).
        if len(samples) < 3:
            return float('inf'), 0.0, 0.0
        vals = [s[1] - baseline for s in samples]
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        std = math.sqrt(var)
        mad = sum(abs(v - mean) for v in vals) / len(vals)
        peak = max(vals) - min(vals)
        # Weighted instability score
        score = std + (0.5 * mad) + (0.1 * peak)
        return score, std, peak

    # ---- environment control (ACE / filament sensors) ----
    def _suspend_ace(self):
        state = {
            'ace': None,
            'runout_active': None,
            'tangle_enabled': None,
            'filament_sensors': [],
        }
        ace = self.printer.lookup_object('ace', None)
        state['ace'] = ace
        if ace is not None:
            try:
                rm = getattr(ace, 'runout_monitor', None)
                if rm is not None:
                    state['runout_active'] = getattr(rm, 'runout_detection_active', None)
                    state['tangle_enabled'] = getattr(rm, 'tangle_detection_enabled', None)
                    if hasattr(rm, 'set_detection_active'):
                        rm.set_detection_active(False)
                    elif hasattr(ace, 'set_runout_detection_active'):
                        ace.set_runout_detection_active(False)
                    else:
                        rm.runout_detection_active = False
                    if hasattr(rm, 'set_tangle_detection_enabled'):
                        rm.set_tangle_detection_enabled(False)
                    elif hasattr(rm, '_set_tangle_detection_enabled'):
                        rm._set_tangle_detection_enabled(False)
                    else:
                        rm.tangle_detection_enabled = False
            except Exception:
                logging.exception("AUTO_PRESSURE_ADVANCE: failed to suspend ACE runout monitor")

        # Best-effort disable filament sensors that may react to calibration extrusion
        for sensor_name in ('filament_runout_nozzle', 'filament_runout_rdm'):
            try:
                self._script('SET_FILAMENT_SENSOR SENSOR=%s ENABLE=0' % sensor_name)
                state['filament_sensors'].append(sensor_name)
            except Exception:
                pass
        return state

    def _restore_ace(self, state):
        if not state:
            return
        for sensor_name in state.get('filament_sensors', []):
            try:
                self._script('SET_FILAMENT_SENSOR SENSOR=%s ENABLE=1' % sensor_name)
            except Exception:
                pass
        ace = state.get('ace')
        if ace is not None:
            try:
                rm = getattr(ace, 'runout_monitor', None)
                if rm is not None:
                    tangle = state.get('tangle_enabled')
                    if tangle is not None:
                        try:
                            if hasattr(rm, 'set_tangle_detection_enabled'):
                                rm.set_tangle_detection_enabled(bool(tangle))
                            elif hasattr(rm, '_set_tangle_detection_enabled'):
                                rm._set_tangle_detection_enabled(bool(tangle))
                            else:
                                rm.tangle_detection_enabled = bool(tangle)
                        except Exception:
                            pass
                    runout = state.get('runout_active')
                    if runout is not None:
                        try:
                            if hasattr(rm, 'set_detection_active'):
                                rm.set_detection_active(bool(runout))
                            elif hasattr(ace, 'set_runout_detection_active'):
                                ace.set_runout_detection_active(bool(runout))
                            else:
                                rm.runout_detection_active = bool(runout)
                        except Exception:
                            pass
            except Exception:
                logging.exception("AUTO_PRESSURE_ADVANCE: failed to restore ACE state")

    # ---- main calibration ----
    def cmd_AUTO_PRESSURE_ADVANCE_CALIBRATE(self, gcmd):
        self._ensure_homed(gcmd)
        sensor = self._lookup_cs1237(gcmd)
        toolhead = self.printer.lookup_object('toolhead')
        extruder_name = self._get_extruder_name(gcmd)
        extruder = self.printer.lookup_object(extruder_name, None)
        if extruder is None:
            raise gcmd.error("Extruder '%s' not found" % (extruder_name,))

        pa_start = gcmd.get_float('PA_START', self.pa_start, minval=0.0)
        pa_end = gcmd.get_float('PA_END', self.pa_end, minval=0.0)
        pa_step = gcmd.get_float('PA_STEP', self.pa_step, above=0.0005)
        if pa_end < pa_start:
            pa_start, pa_end = pa_end, pa_start

        extruder_temp = gcmd.get_float('EXTRUDER_TEMP', self.extruder_temp,
                                       above=0.0)
        bed_temp = gcmd.get_float('BED_TEMP', self.bed_temp)
        extrude_length = gcmd.get_float('EXTRUDE_LENGTH', self.extrude_length,
                                        above=1.0)
        speed_slow = gcmd.get_float('SPEED_SLOW', self.speed_slow, above=0.5)
        speed_fast = gcmd.get_float('SPEED_FAST', self.speed_fast, above=1.0)
        cycles = gcmd.get_int('CYCLES', self.cycles, minval=1, maxval=10)
        settle = gcmd.get_float('SETTLE_TIME', self.settle_time, minval=0.0)
        save = gcmd.get_int('SAVE', 1 if self.save_config else 0, minval=0,
                            maxval=1)
        test_x = gcmd.get_float('TEST_X', self.test_x)
        test_y = gcmd.get_float('TEST_Y', self.test_y)
        test_z = gcmd.get_float('TEST_Z', self.test_z, above=5.0)

        pa_values = []
        v = pa_start
        while v <= pa_end + (pa_step * 0.5):
            pa_values.append(round(v, 6))
            v += pa_step
        if not pa_values:
            pa_values = [pa_start]

        slow_len = extrude_length * self.slow_ratio
        fast_len = extrude_length - 2.0 * slow_len
        if fast_len < 1.0:
            slow_len = extrude_length * 0.25
            fast_len = extrude_length * 0.5

        status = extruder.get_status(self.reactor.monotonic())
        orig_pa = status.get('pressure_advance', 0.0)
        orig_smooth = status.get('smooth_time', None)

        gcmd.respond_info(
            "AUTO_PRESSURE_ADVANCE: CS1237-based calibration\n"
            "  sensor=%s, extruder=%s\n"
            "  PA range %.4f..%.4f step %.4f (%d values), cycles=%d\n"
            "  extrude %.2fmm (slow %.2f/fast %.2f mm/s), test at X%.2f Y%.2f Z%.2f\n"
            "  extruder_temp=%.1f%s"
            % (self.sensor_name, extruder_name, pa_start, pa_values[-1],
               pa_step, len(pa_values), cycles, extrude_length,
               speed_slow, speed_fast, test_x, test_y, test_z,
               extruder_temp,
               (" bed_temp=%.1f" % bed_temp) if bed_temp is not None else ""))

        collector = self._SampleCollector()
        results = []
        sensor_enabled = False
        ace_state = None

        gcode_move = self.printer.lookup_object('gcode_move')
        try:
            st = gcode_move.get_status()
            orig_abs = st.get('absolute_coordinates',
                              getattr(gcode_move, 'absolute_coord', True))
            orig_e_abs = st.get('absolute_extrude',
                                getattr(gcode_move, 'allow_absolute_extrude', True))
        except Exception:
            orig_abs = getattr(gcode_move, 'absolute_coord', True)
            orig_e_abs = getattr(gcode_move, 'allow_absolute_extrude', True)

        try:
            # Suspend ACE/runout monitoring and filament sensors to avoid
            # interference during calibration extrusion moves.
            ace_state = self._suspend_ace()
            if ace_state.get('filament_sensors') or ace_state.get('ace') is not None:
                gcmd.respond_info(
                    "AUTO_PRESSURE_ADVANCE: suspended ACE/runout monitoring for calibration")
            # Heat
            if bed_temp is not None:
                self._script("M140 S%.1f" % bed_temp)
            self._script("M104 S%.1f" % extruder_temp)
            if bed_temp is not None:
                gcmd.respond_info("Waiting for bed temperature...")
                self._script("M190 S%.1f" % bed_temp)
            gcmd.respond_info("Waiting for extruder temperature...")
            self._script("M109 S%.1f" % extruder_temp)

            # Position safely for in-air extrusion
            self._script("G90")
            self._script("M83")
            self._script("G92 E0")
            self._script("G1 Z%.3f F3000" % (max(test_z, 20.0),))
            self._script("G1 X%.3f Y%.3f F6000" % (test_x, test_y))

            # Enable CS1237 and collect baseline
            self._enable_sensor_reporting(sensor)
            sensor_enabled = True
            try:
                sensor.add_client(collector.cb)
            except Exception:
                pass

            collector.clear()
            self._pause(max(settle, 0.8))
            baseline_samples = list(collector.samples)
            if baseline_samples:
                baseline = sum(s[1] for s in baseline_samples) / len(baseline_samples)
            else:
                # fallback to current status
                st = sensor.get_status(self.reactor.monotonic()) if hasattr(sensor, 'get_status') else {}
                baseline = float(st.get('adc', 0.0) or 0.0)
            gcmd.respond_info(
                "CS1237 baseline ADC: %.3f (%d samples)"
                % (baseline, len(baseline_samples)))

            # Prime filament
            if self.prime_length > 0:
                self._script("G1 E%.4f F%.1f" % (self.prime_length, 120.0))
                self._script("G92 E0")
                self._pause(settle)

            for pa in pa_values:
                self._set_pa(extruder_name, pa)
                collector.clear()
                toolhead.wait_moves()

                # Run extrusion cycles: slow->fast->slow to create PA-sensitive
                # pressure transitions while sampling CS1237.
                for c in range(cycles):
                    self._script("G92 E0")
                    self._script("G1 E%.5f F%.1f" % (slow_len, speed_slow * 60.0))
                    self._script("G1 E%.5f F%.1f" % (fast_len, speed_fast * 60.0))
                    self._script("G1 E%.5f F%.1f" % (slow_len, speed_slow * 60.0))
                toolhead.wait_moves()
                self._pause(settle)

                samples = list(collector.samples)
                score, std, peak = self._score_samples(samples, baseline)
                results.append({
                    'pa': pa,
                    'score': score,
                    'std': std,
                    'peak': peak,
                    'count': len(samples),
                })
                gcmd.respond_info(
                    "  PA %.4f: score=%.4f std=%.4f peak=%.4f samples=%d"
                    % (pa, score, std, peak, len(samples)))

                # Retract/recover to limit oozing/stringing between tests
                if self.retract_length > 0:
                    self._script("G1 E-%.4f F%.1f" % (
                        self.retract_length, self.retract_speed * 60.0))
                    self._pause(settle)
                    self._script("G1 E%.4f F%.1f" % (
                        self.retract_length, self.retract_speed * 60.0))
                    self._script("G92 E0")

            if not results:
                raise gcmd.error("AUTO_PRESSURE_ADVANCE: no results collected")

            best = min(results, key=lambda r: r['score'])
            best_pa = best['pa']

            # Restore movement modes
            if orig_abs:
                self._script("G90")
            else:
                self._script("G91")
            if orig_e_abs:
                self._script("M82")
            else:
                self._script("M83")

            # Apply best result
            self._set_pa(extruder_name, best_pa, orig_smooth)
            gcmd.respond_info(
                "AUTO_PRESSURE_ADVANCE best result (lowest CS1237 force variation):\n"
                "  pressure_advance=%.6f score=%.4f std=%.4f peak=%.4f samples=%d"
                % (best_pa, best['score'], best['std'], best['peak'],
                   best['count']))

            if save:
                self._save_pa(extruder_name, best_pa, orig_smooth)
                gcmd.respond_info(
                    "The SAVE_CONFIG command will update the printer config file\n"
                    "with these parameters and restart the printer.")
            else:
                gcmd.respond_info(
                    "SAVE=0: value applied for this session but not written to config.")

        finally:
            try:
                if sensor_enabled:
                    try:
                        sensor.remove_client(collector.cb)
                    except Exception:
                        pass
                    self._disable_sensor_reporting(sensor)
            except Exception:
                logging.exception("AUTO_PRESSURE_ADVANCE: sensor cleanup failed")
            try:
                self._restore_ace(ace_state)
            except Exception:
                logging.exception("AUTO_PRESSURE_ADVANCE: ACE restore failed")
            try:
                self._set_pa(extruder_name, orig_pa, orig_smooth)
            except Exception:
                pass
            # Re-apply chosen PA if we selected one (restore above may have
            # overwritten in some flows; ensure final is best when saved/applied)
            try:
                if results:
                    best_pa = min(results, key=lambda r: r['score'])['pa']
                    self._set_pa(extruder_name, best_pa, orig_smooth)
            except Exception:
                pass
            try:
                if orig_abs:
                    self._script("G90")
                else:
                    self._script("G91")
                if orig_e_abs:
                    self._script("M82")
                else:
                    self._script("M83")
            except Exception:
                pass

    def cmd_AUTO_PRESSURE_ADVANCE_SET(self, gcmd):
        extruder_name = self._get_extruder_name(gcmd)
        extruder = self.printer.lookup_object(extruder_name, None)
        if extruder is None:
            raise gcmd.error("Extruder '%s' not found" % (extruder_name,))
        status = extruder.get_status(self.reactor.monotonic())
        pa = gcmd.get_float('ADVANCE', status.get('pressure_advance', 0.0),
                            minval=0.0)
        smooth = gcmd.get_float('SMOOTH_TIME', status.get('smooth_time', None))
        save = gcmd.get_int('SAVE', 0, minval=0, maxval=1)
        self._set_pa(extruder_name, pa, smooth)
        gcmd.respond_info(
            "Set %s pressure_advance=%.6f%s"
            % (extruder_name, pa,
               (" smooth_time=%.6f" % smooth) if smooth is not None else ""))
        if save:
            self._save_pa(extruder_name, pa, smooth)
            gcmd.respond_info(
                "The SAVE_CONFIG command will update the printer config file\n"
                "with these parameters and restart the printer.")


def load_config(config):
    return AutoPressureAdvance(config)
