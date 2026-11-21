# Automatic Z offset calibration for load-cell / contact probes
#
# This module probes the bed using the configured probe (e.g. probe_ks1 with a
# CS1237 strain gauge) and calculates a Z offset from the detected contact
# point. It is designed for printers that home Z with a virtual endstop and a
# nozzle/load-cell contact probe.
#
# Copyright (C) 2026
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging


class AutoZOffset:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name()
        self.gcode = self.printer.lookup_object('gcode')

        # Compensation added to the automatic calculation (mm). REQUIRED.
        # AUTO_Z_OFFSET computes a fresh offset from each probe trigger:
        #   new_z_offset = trigger_z - compensation
        # For probe_ks1 on probe:z_virtual_endstop (this printer's setup):
        #   compensation >  0.00 : more gap / nozzle further from bed (fixes
        #                          scraping) -> makes z_offset more negative
        #   compensation <  0.00 : less gap / nozzle closer to bed
        #   compensation =  0.00 : treat detected contact as Z=0
        # If the nozzle scrapes, INCREASE compensation.
        self.contact_compensation = self._get_required_float(
            config, 'contact_compensation')

        # Optional probe object name. Defaults to the standard "probe" object.
        self.probe_name = config.get('probe_name', 'probe')

        # Optional probing location. If not set, probes at current XY.
        self.probe_x = self._get_optional_float(config, 'probe_x', None)
        self.probe_y = self._get_optional_float(config, 'probe_y', None)

        # Whether to save the calculated offset to printer.cfg on success.
        self.save_config = config.getboolean('save_config', True)

        # Where to save the offset. Defaults to the active probe's config name
        # (e.g. probe_ks1). Set this if you need to target a specific section.
        self.offset_section = self._get_optional_str(config, 'offset_section')
        self.offset_option = config.get('offset_option', 'z_offset')

        self.speed = self._get_optional_float(config, 'speed', None, above=0.)
        self.lift_speed = self._get_optional_float(
            config, 'lift_speed', None, above=0.)
        self.samples = self._get_optional_int(config, 'samples', None, minval=1)
        self.sample_retract_dist = self._get_optional_float(
            config, 'sample_retract_dist', None, above=0.)
        self.samples_tolerance = self._get_optional_float(
            config, 'samples_tolerance', None, minval=0.)
        self.samples_retries = self._get_optional_int(
            config, 'samples_tolerance_retries', None, minval=0)
        self.samples_result = self._get_optional_str(config, 'samples_result')

        self.gcode.register_command(
            'AUTO_Z_OFFSET', self.cmd_AUTO_Z_OFFSET,
            desc=self.cmd_AUTO_Z_OFFSET_help)
        self.gcode.register_command(
            'AUTO_Z_OFFSET_CALIBRATE', self.cmd_AUTO_Z_OFFSET,
            desc=self.cmd_AUTO_Z_OFFSET_help)
        self.gcode.register_command(
            'AUTO_Z_OFFSET_LEARN', self.cmd_AUTO_Z_OFFSET_LEARN,
            desc=self.cmd_AUTO_Z_OFFSET_LEARN_help)

    def _get_optional_str(self, config, option):
        value = config.get(option, None)
        if value is None:
            return None
        value = str(value).strip()
        return value if value else None

    def _parse_float(self, raw, option, config):
        cleaned = str(raw).strip().replace(',', '.').replace('\u2212', '-')
        for suffix in ('mm/s', 'mm', 's'):
            if cleaned.lower().endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
        try:
            return float(cleaned)
        except (TypeError, ValueError):
            raise config.error(
                "Option '%s' in section '%s' must be a number (got '%s'). "
                "Use a plain value like 0.08 (no 'mm' suffix, use '.' for "
                "decimals)." % (option, config.get_name(), raw))

    def _get_required_float(self, config, option, minval=None, maxval=None,
                            above=None, below=None):
        raw = config.get(option)
        value = self._parse_float(raw, option, config)
        if minval is not None and value < minval:
            raise config.error(
                "Option '%s' in section '%s' must be at least %s"
                % (option, config.get_name(), minval))
        if maxval is not None and value > maxval:
            raise config.error(
                "Option '%s' in section '%s' must be at most %s"
                % (option, config.get_name(), maxval))
        if above is not None and value <= above:
            raise config.error(
                "Option '%s' in section '%s' must be above %s"
                % (option, config.get_name(), above))
        if below is not None and value >= below:
            raise config.error(
                "Option '%s' in section '%s' must be below %s"
                % (option, config.get_name(), below))
        return value

    def _get_optional_float(self, config, option, default, minval=None,
                            maxval=None, above=None, below=None):
        raw = config.get(option, None)
        if raw is None:
            return default
        raw = str(raw).strip()
        if raw == '':
            return default
        try:
            value = self._parse_float(raw, option, config)
        except Exception:
            logging.warning(
                "auto_z_offset: unable to parse '%s: %s', using %r",
                option, raw, default)
            return default
        if minval is not None and value < minval:
            return default
        if maxval is not None and value > maxval:
            return default
        if above is not None and value <= above:
            return default
        if below is not None and value >= below:
            return default
        return value

    def _get_optional_int(self, config, option, default, minval=None,
                          maxval=None):
        raw = config.get(option, None)
        if raw is None:
            return default
        raw = str(raw).strip()
        if raw == '':
            return default
        try:
            value = int(float(raw.replace(',', '.').replace('\u2212', '-')))
        except (TypeError, ValueError):
            logging.warning(
                "auto_z_offset: unable to parse '%s: %s', using %r",
                option, raw, default)
            return default
        if minval is not None and value < minval:
            return default
        if maxval is not None and value > maxval:
            return default
        return value

    cmd_AUTO_Z_OFFSET_help = (
        "Automatically probe and set the probe Z offset. "
        "Parameters: COMPENSATION=<mm> SAMPLES=<n> SPEED=<mm/s> "
        "LIFT_SPEED=<mm/s> SAMPLE_RETRACT_DIST=<mm> SAVE=<0|1>")
    cmd_AUTO_Z_OFFSET_LEARN_help = (
        "Apply current baby-step Z offset to probe z_offset and learn "
        "contact_compensation. Parameters: SAVE=<0|1> CLEAR=<0|1>")

    def _lookup_probe(self, gcmd):
        probe = self.printer.lookup_object(self.probe_name, None)
        if probe is None:
            raise gcmd.error(
                "AUTO_Z_OFFSET: probe '%s' not found" % (self.probe_name,))
        return probe

    def _ensure_homed_z(self, gcmd):
        toolhead = self.printer.lookup_object('toolhead')
        curtime = self.printer.get_reactor().monotonic()
        homed_axes = toolhead.get_status(curtime).get('homed_axes', '')
        if 'z' not in homed_axes:
            raise gcmd.error(
                "AUTO_Z_OFFSET: Z axis must be homed before calibration")
        if self.probe_x is not None or self.probe_y is not None:
            if 'x' not in homed_axes or 'y' not in homed_axes:
                raise gcmd.error(
                    "AUTO_Z_OFFSET: X and Y must be homed when probe_x/probe_y "
                    "are configured")

    def _move_to_probe_xy(self, gcmd, probe):
        if self.probe_x is None and self.probe_y is None:
            return
        toolhead = self.printer.lookup_object('toolhead')
        pos = toolhead.get_position()
        params = self._effective_probe_params(gcmd, probe)
        if self.probe_x is not None:
            pos[0] = self.probe_x
        if self.probe_y is not None:
            pos[1] = self.probe_y
        lift_speed = params.get('lift_speed', params.get('probe_speed', 5.))
        toolhead.manual_move(pos, lift_speed)

    def _effective_probe_params(self, gcmd, probe):
        params = {}
        get_probe_params = getattr(probe, 'get_probe_params', None)
        if get_probe_params is not None:
            try:
                params = dict(get_probe_params(gcmd) or {})
            except Exception:
                params = {}
        return params

    def _run_probe(self, gcmd, probe):
        # Use the probe's session API (compatible with mainline-style probes in
        # this fork, including probe_ks1).
        start = getattr(probe, 'start_probe_session', None)
        if start is None:
            raise gcmd.error(
                "AUTO_Z_OFFSET: probe '%s' does not support probe sessions"
                % (self.probe_name,))
        probe_session = start(gcmd)
        probe_session.run_probe(gcmd)
        results = probe_session.pull_probed_results()
        probe_session.end_probe_session()
        if not results:
            raise gcmd.error("AUTO_Z_OFFSET: probe returned no results")
        return results[0]

    def _build_probe_gcmd(self, gcmd):
        # Build a gcode command that applies configured defaults while allowing
        # explicit gcode parameters to override them.
        try:
            raw = dict(gcmd.get_command_parameters())
        except Exception:
            raw = {}
        defaults = {
            'SAMPLES': self.samples,
            'SAMPLE_RETRACT_DIST': self.sample_retract_dist,
            'SPEED': self.speed,
            'PROBE_SPEED': self.speed,
            'LIFT_SPEED': self.lift_speed,
            'SAMPLES_TOLERANCE': self.samples_tolerance,
            'SAMPLES_TOLERANCE_RETRIES': self.samples_retries,
            'SAMPLES_RESULT': self.samples_result,
        }
        for key, value in defaults.items():
            if value is None:
                continue
            if key not in raw:
                raw[key] = value
        return self.gcode.create_gcode_command(
            gcmd.get_command() or 'AUTO_Z_OFFSET', gcmd.get_commandline(), raw)

    def _resolve_offset_section(self, probe):
        if self.offset_section:
            return self.offset_section
        cmd_helper = getattr(probe, 'cmd_helper', None)
        name = getattr(cmd_helper, 'name', None)
        if name:
            return name
        return getattr(probe, 'name', self.probe_name)

    def cmd_AUTO_Z_OFFSET(self, gcmd):
        probe = self._lookup_probe(gcmd)
        self._ensure_homed_z(gcmd)
        self._move_to_probe_xy(gcmd, probe)

        compensation = gcmd.get_float(
            'COMPENSATION', self.contact_compensation)
        save = gcmd.get_int('SAVE', 1 if self.save_config else 0, minval=0,
                            maxval=1)

        probe_gcmd = self._build_probe_gcmd(gcmd)
        ppos = self._run_probe(probe_gcmd, probe)

        trigger_z = float(ppos.test_z)
        reported_bed_z = float(ppos.bed_z)

        offsets = (0., 0., 0.)
        get_offsets = getattr(probe, 'get_offsets', None)
        if get_offsets is not None:
            try:
                offsets = get_offsets(probe_gcmd)
            except Exception:
                offsets = (0., 0., 0.)
        current_z_offset = float(offsets[2]) if len(offsets) > 2 else 0.0

        # Calculate z_offset fresh from this probe trigger every time (do not
        # incrementally adjust the existing z_offset). `trigger_z` is the
        # toolhead Z at the detected contact/trigger point in the current
        # coordinate system.
        #   new = trigger_z - compensation
        # For probe:z_virtual_endstop here, a MORE NEGATIVE z_offset means the
        # nozzle is further from the bed (more gap). Therefore:
        # compensation > 0  => more gap / fixes scraping (z_offset more negative)
        # compensation < 0  => less gap / closer to bed
        # compensation == 0 => treat detected contact as Z=0
        new_z_offset = trigger_z - compensation

        section = self._resolve_offset_section(probe)
        gcmd.respond_info(
            "AUTO_Z_OFFSET results:\n"
            "  probe: %s\n"
            "  config defaults: samples=%s speed=%s lift=%s retract=%s\n"
            "  trigger toolhead Z: %.6f\n"
            "  reported bed Z (current offset, diagnostic): %.6f\n"
            "  current z_offset (diagnostic): %.6f\n"
            "  compensation: %.6f\n"
            "  calculated z_offset (fresh): trigger_z - compensation = %.6f\n"
            "  target config: [%s] %s"
            % (self.probe_name, self.samples, self.speed, self.lift_speed,
               self.sample_retract_dist,
               trigger_z, reported_bed_z, current_z_offset,
               compensation, new_z_offset, section, self.offset_option))

        if save:
            configfile = self.printer.lookup_object('configfile')
            configfile.set(section, self.offset_option, "%.6f" % (new_z_offset,))
            gcmd.respond_info(
                "The SAVE_CONFIG command will update the printer config file\n"
                "with the above and restart the printer.")
        else:
            gcmd.respond_info(
                "SAVE=0: calculated value was not written to config.")

    def cmd_AUTO_Z_OFFSET_LEARN(self, gcmd):
        probe = self._lookup_probe(gcmd)
        save = gcmd.get_int('SAVE', 1 if self.save_config else 0, minval=0,
                            maxval=1)
        clear = gcmd.get_int('CLEAR', 1, minval=0, maxval=1)

        gcode_move = self.printer.lookup_object('gcode_move', None)
        if gcode_move is None:
            raise gcmd.error("AUTO_Z_OFFSET_LEARN: gcode_move not available")
        babystep = float(gcode_move.get_status()['homing_origin'].z)
        if abs(babystep) < 0.000001:
            raise gcmd.error(
                "AUTO_Z_OFFSET_LEARN: Z baby-step/gcode offset is 0; "
                "nothing to learn")

        get_offsets = getattr(probe, 'get_offsets', None)
        if get_offsets is None:
            raise gcmd.error(
                "AUTO_Z_OFFSET_LEARN: probe does not expose get_offsets()")
        current_z_offset = float(get_offsets(gcmd)[2])
        section = self._resolve_offset_section(probe)

        # Apply baby-step to probe z_offset (same direction as Z_OFFSET_APPLY_PROBE):
        #   new_probe_z_offset = current_probe_z_offset - babystep
        # Positive babystep (nozzle moved up / more gap) makes probe z_offset
        # more negative on this virtual-endstop setup.
        new_z_offset = current_z_offset - babystep
        # Persist into contact_compensation so future AUTO_Z_OFFSET runs keep it:
        #   effective = base - compensation  => compensation += babystep
        new_compensation = self.contact_compensation + babystep

        gcmd.respond_info(
            "AUTO_Z_OFFSET_LEARN:\n"
            "  babystep/gcode Z offset: %.6f\n"
            "  current probe z_offset: %.6f\n"
            "  new probe z_offset: %.6f\n"
            "  current contact_compensation: %.6f\n"
            "  new contact_compensation: %.6f\n"
            "  target config: [%s] %s, [%s] contact_compensation"
            % (babystep, current_z_offset, new_z_offset,
               self.contact_compensation, new_compensation,
               section, self.offset_option, self.name))

        if save:
            configfile = self.printer.lookup_object('configfile')
            configfile.set(section, self.offset_option, "%.6f" % (new_z_offset,))
            configfile.set(self.name, 'contact_compensation',
                           "%.6f" % (new_compensation,))
            self.contact_compensation = new_compensation
            gcmd.respond_info(
                "The SAVE_CONFIG command will update the printer config file\n"
                "with the above and restart the printer.")
            if clear:
                self.gcode.run_script_from_command('SET_GCODE_OFFSET Z=0 MOVE=0')
                gcmd.respond_info(
                    "Cleared runtime gcode Z offset (SET_GCODE_OFFSET Z=0).")
        else:
            gcmd.respond_info(
                "SAVE=0: calculated values were not written to config.")


def load_config(config):
    return AutoZOffset(config)
