# `auto_z_offset` (Klipper extra)

`auto_z_offset` is a Klipper plugin for printers that use a **contact/load-cell probe** (such as `probe_ks1` with a CS1237 strain gauge) and home Z with a **virtual endstop** (`probe:z_virtual_endstop`). It automatically probes the bed, calculates a `z_offset` for the active probe, and can save it to `printer.cfg`.

This was written for a Kobra 3 Max–style setup using a custom Klipper fork (`probe_ks1` + `cs1237`), but it should work with any probe in that fork that implements the standard probe session API (`start_probe_session` / `run_probe` / `pull_probed_results` / `end_probe_session`).

## Files

- Plugin: `klippy/extras/auto_z_offset.py`
- Install it into the Klipper installation that actually runs on your printer (for example `~/klipper/klippy/extras/auto_z_offset.py`), alongside modules like `probe_ks1.py` and `cs1237.py`.

After copying/updating the file, restart Klipper:

```gcode
FIRMWARE_RESTART
```

## How it works

1. **Probe contact:** The command uses the configured probe object (default: `probe`). On a `probe_ks1`/CS1237 setup, the nozzle/toolhead contacts the bed and the strain-gauge probe triggers.
2. **Read probe result:** The plugin runs a probe session and reads the probe result:
   - `trigger toolhead Z` (`ppos.test_z`): toolhead Z at the trigger point in the current coordinate system.
   - `reported bed Z` (`ppos.bed_z`): the probe’s estimated bed contact Z using the *current* probe offset.
   - `current z_offset`: the probe’s current configured Z offset (e.g. `[probe_ks1] z_offset`).
3. **Calculate a new offset (fresh each run):** It computes a new Z offset from the probe trigger every time it runs; it does **not** incrementally adjust the existing `z_offset`.

   ```text
   new_z_offset = trigger_z - contact_compensation
   ```

   (`trigger_z` is the toolhead Z at the detected contact/trigger point.)

4. **Save (optional):** With `SAVE=1` (default if `save_config: True`), it writes the calculated value to the probe’s config section/option (by default `[probe_ks1] z_offset`) and prints a reminder to run `SAVE_CONFIG`.

### Z offset direction (important for this setup)

On this `probe:z_virtual_endstop` / `probe_ks1` setup, the probe’s `z_offset` is used as the virtual Z endstop position. That means:

- **More negative `z_offset`** (example: `-0.475` → `-0.525`) = nozzle **further from the bed** / more gap (helps if scraping).
- **Less negative / more positive `z_offset`** (example: `-0.475` → `-0.425`) = nozzle **closer to the bed** (can cause scraping).

Because of that, the plugin interprets `contact_compensation` as:

- `contact_compensation > 0` → **more gap** / nozzle further from bed (makes `z_offset` more negative)
- `contact_compensation < 0` → **less gap** / nozzle closer to bed
- `contact_compensation = 0` → treat detected contact as `Z=0`

If the nozzle scrapes, **increase** `contact_compensation`.

> `contact_compensation` is a manual tuning value. The probe can detect contact, but it cannot by itself know your ideal first-layer squish, thermal expansion, or surface-specific behavior.

## Configuration

Add an `[auto_z_offset]` section to `printer.cfg`:

```ini
[auto_z_offset]
# REQUIRED. Manual tuning value in mm.
# AUTO_Z_OFFSET computes a fresh offset from each probe trigger:
#   new_z_offset = trigger_z - contact_compensation
#   > 0 : more gap / further from bed (fixes scraping)
#   < 0 : closer to bed
#   = 0 : treat detected contact as Z=0
contact_compensation: 0.0

# Save calculated z_offset to printer.cfg on success (default: True)
save_config: True

# Probe object to use (default: probe)
# probe_name: probe

# Optional fixed probing location. If omitted, probes at current XY.
# If set, X and Y must be homed.
# probe_x: 210
# probe_y: 210

# Optional probe defaults (command parameters override these)
# samples: 3
# speed: 3
# lift_speed: 8
# sample_retract_dist: 2
# samples_tolerance: 0.01
# samples_tolerance_retries: 3
# samples_result: median

# Optional config target (defaults to the active probe section, e.g. probe_ks1)
# offset_section: probe_ks1
# offset_option: z_offset
```

Notes:
- Use a plain numeric value for `contact_compensation` (example: `0.08` or `-0.2`). Do **not** add `mm`. Use `.` for decimals.
- `contact_compensation` is required. Klipper will report a clear config error if it is missing or not parseable.

## Commands

### `AUTO_Z_OFFSET` / `AUTO_Z_OFFSET_CALIBRATE`

Probes and calculates/saves the probe Z offset.

```gcode
G28
AUTO_Z_OFFSET
```

Common form:

```gcode
G28
AUTO_Z_OFFSET COMPENSATION=0.08 SAMPLES=3 SPEED=3 LIFT_SPEED=8 SAMPLE_RETRACT_DIST=2 SAVE=1
SAVE_CONFIG
```

Parameters:
- `COMPENSATION=<mm>`: overrides `[auto_z_offset] contact_compensation` for this run.
- `SAMPLES=<n>`
- `SPEED=<mm/s>` / `PROBE_SPEED=<mm/s>`
- `LIFT_SPEED=<mm/s>`
- `SAMPLE_RETRACT_DIST=<mm>`
- `SAMPLES_TOLERANCE=<mm>`
- `SAMPLES_TOLERANCE_RETRIES=<n>`
- `SAMPLES_RESULT=<median|average>` (as supported by the probe)
- `SAVE=<0|1>`: `1` writes the result to config; `0` reports only.

Requirements/safety:
- Z must be homed. X/Y must be homed if `probe_x`/`probe_y` are configured.
- Probe only when it is safe: clean nozzle, clear bed area, and use representative temperatures if you want a thermally relevant offset.
- Review the console output before `SAVE_CONFIG`.

Example output includes: trigger toolhead Z, reported bed Z, current `z_offset`, compensation, calculated `z_offset`, and target config section.

### `AUTO_Z_OFFSET_LEARN`

Learns from your current baby-step/gcode Z offset (after you manually tune a first layer) and saves the adjustment.

```gcode
AUTO_Z_OFFSET_LEARN SAVE=1
SAVE_CONFIG
```

Parameters:
- `SAVE=<0|1>` (default follows `save_config`)
- `CLEAR=<0|1>` (default `1`): clears runtime Z gcode offset after applying (`SET_GCODE_OFFSET Z=0 MOVE=0`).

What it does:
- Reads `gcode_move.homing_origin.z` (baby-step Z offset).
- Applies it to the probe `z_offset`: `new_probe_z_offset = current_probe_z_offset - babystep`.
- Updates `[auto_z_offset] contact_compensation`: `new_contact_compensation = current_contact_compensation + babystep`, so future `AUTO_Z_OFFSET` runs preserve the learned correction.
- Saves `[probe_ks1] z_offset` (or resolved target) and `[auto_z_offset] contact_compensation` when `SAVE=1`.

This is the recommended way to “auto-tune” compensation from real first-layer feedback.

## Finding the right `contact_compensation`

### Manual iterative method
1. Heat the bed/nozzle to normal print temperatures and clean the nozzle.
2. Home and run a safe starting calibration:
   ```gcode
   G28
   AUTO_Z_OFFSET COMPENSATION=0.10 SAMPLES=3 SAVE=1
   SAVE_CONFIG
   ```
3. Print a first-layer test.
4. Adjust:
   - scraping / too close → **increase** `contact_compensation`
   - too high / poor adhesion → **decrease** `contact_compensation`
5. Repeat in small steps (about `0.02–0.05 mm`).

### Back-calculate from a known-good `z_offset`
If you already know a good probe Z offset (`Z_good`):

1. Run:
   ```gcode
   G28
   AUTO_Z_OFFSET COMPENSATION=0.0 SAMPLES=3 SAVE=0
   ```
2. Take `calculated z_offset` from the output as `Z_auto0`.
3. Compute:

   ```text
   contact_compensation = Z_auto0 - Z_good
   ```

Example: `Z_auto0 = -0.420`, `Z_good = -0.480` → `contact_compensation = 0.060`.

### Learn from baby stepping
1. Run `AUTO_Z_OFFSET` with a safe compensation and save.
2. Tune the first layer with baby stepping.
3. Run `AUTO_Z_OFFSET_LEARN SAVE=1` and `SAVE_CONFIG`.

## Troubleshooting

### `Unable to parse option 'contact_compensation' in section 'auto_z_offset'`
- Make sure the **updated** `auto_z_offset.py` is installed in the Klipper instance that is actually running, then restart Klipper.
- Check the `[auto_z_offset]` section in the *printer’s* active `printer.cfg`:
  - use `contact_compensation: 0.08` (no `mm`)
  - use a decimal point (`0.08`, not `0,08`)
  - avoid stray characters/smart quotes/Unicode minus
- As a recovery step, temporarily comment out `[auto_z_offset]` to let Klipper boot, fix the config/plugin, then re-enable.

### Nozzle scrapes the bed
- For this setup, move toward **more gap**: increase `contact_compensation`, or make `[probe_ks1] z_offset` **more negative**.
- Re-run with `SAVE=0` first if you want to inspect the calculated offset before saving.
- Emergency temporary lift (does not fix probe calibration):
  ```gcode
  SET_GCODE_OFFSET Z=0.10 MOVE=1
  ```
  Reset after testing: `SET_GCODE_OFFSET Z=0 MOVE=1`.

### Results vary between runs
- Clean the nozzle and bed contact area.
- Probe at consistent temperatures.
- Increase `SAMPLES` (e.g. `3`–`5`) and/or use slower probe speeds if appropriate for your `probe_ks1`/CS1237 setup.
- Verify CS1237/probe configuration and physical condition; `contact_compensation` cannot compensate for inconsistent triggering.

## Limitations

- `AUTO_Z_OFFSET` automates **measurement and offset calculation**, not the human judgment of a perfect first layer. `contact_compensation` (or a learning step like `AUTO_Z_OFFSET_LEARN`) is still required.
- Fully automatic determination of ideal squish from a contact trigger alone is unreliable; closed-loop methods would require additional sensing/analysis beyond this plugin’s scope.
- After saving, `SAVE_CONFIG`/restart is required for Klipper to load the updated config values.