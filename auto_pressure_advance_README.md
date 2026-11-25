# `auto_pressure_advance` (Klipper extra)

`auto_pressure_advance` is a Klipper plugin that **automatically calibrates
Pressure Advance (PA)** by watching the nozzle force reported by the
**CS1237 load cell** while the printer performs a controlled
acceleration/deceleration extrusion.

It is written for the Kobra 3 Max / custom Klipper fork setup using
`[cs1237]` (toolhead load cell) and a standard Klipper extruder with
`SET_PRESSURE_ADVANCE`.

## Files

- Plugin: `klippy/extras/auto_pressure_advance.py`
- Install it into the Klipper installation that actually runs on your
  printer (for example `~/klipper/klippy/extras/auto_pressure_advance.py`),
  alongside modules like `cs1237.py`, then restart Klipper:

```gcode
FIRMWARE_RESTART
```

## How it works

1. **The physics.** Klipper implements pressure advance by adding

   ```text
   pa_position(t) = nominal_position(t) + pressure_advance * nominal_velocity(t)
   ```

   to the extruder position (`klippy/chelper/kin_extruder.c`).  PA therefore
   only does something where the *velocity changes* - during the
   acceleration and deceleration ramps of a move.  A move at constant
   velocity is completely unaffected by PA.

   Physically the filament needs a little time (the *filament travel
   delay*) to reach the melt chamber.  When the toolhead accelerates, the
   chamber is briefly starved and the nozzle pressure dips; when it
   decelerates, the chamber is briefly overfilled and the pressure rises.
   PA compensates exactly that delay by pushing extra filament during the
   acceleration ramp and pulling it back during the deceleration ramp.

   **The correct PA is the one where the two transients cancel each other
   and the nozzle pressure simply follows the flow ramp.**  The plugin
   therefore looks for the PA value that produces the *smoothest* force
   trace.

2. **The test move.**  In this fork Klipper only applies PA to moves that
   contain X or Y motion (`kinematics/extruder.py`: `can_pressure_advance`).
   A pure `G1 E...` move receives **no** pressure advance at all and cannot
   be used for the measurement, so the plugin performs a short XY move with
   an extrusion component:

   ```gcode
   G1 X15.0000 E0.9375 F2400
   ```

   The extrusion amount is derived from the requested filament speed, the
   move speed and the acceleration ratio, so the acceleration ramp has a
   well defined length of `1 / accel_ratio` seconds.

3. **The measurement.**  While the move runs, the plugin samples the load
   cell at `sample_rate` Hz and afterwards removes the slow part of the
   signal with a moving average (`window_ratio` times the acceleration
   ramp).  The remaining high frequency content is the *score*: it is
   dominated by the two transients described above, is minimal when they
   cancel, and is completely insensitive to small differences in the
   sampling phase.

4. **The sweep.**  The plugin measures the score for every pressure
   advance in `pa_start .. pa_end`, then refines the search around the
   best value (`refine_passes`, `refine_ratio`) and fits a parabola
   through the three points around the minimum for the final value.  The
   best value is applied immediately and, by default, written to
   `printer.cfg` automatically.  Klipper performs a `SAVE_CONFIG` and restarts
   once the printer is idle; pass `SAVE=0` or set `auto_save_config: False`
   to keep the value in memory only.

5. **Safety.**  The calibration requires homed axes, refuses to run while
   a print is active, heats the nozzle to `extruder_temp` and moves to a
   safe in-air test position.  Filament runout sensors and the ACE Pro
   runout/tangle monitoring are suspended for the duration of the test so
   that the calibration extrusion cannot trigger a runout or a tool change.
   Everything is restored afterwards, including the toolhead velocity
   limits.

## Configuration

Add to `printer.cfg`:

```ini
[auto_pressure_advance]
# Load cell object providing the force readings
sensor: cs1237

# Extruder whose pressure advance is measured
extruder: extruder

# Safe in-air extrusion position (the filament droops - clean up afterwards)
test_x: 210
test_y: 210
test_z: 25
# use_test_position: True

# Temperature for the test
extruder_temp: 220
# bed_temp: 0

# Test move geometry
filament_speed: 2.5      # mm/s of filament (2.5 mm/s ~ 6 mm3/s of flow)
accel_ratio: 10.0        # acceleration / speed (1/s) -> 100 ms ramp
move_speed: 40.0         # mm/s of the toolhead move
move_length: 15.0        # mm of travel during the test move
prime_length: 5.0        # mm of filament used to prime the extruder
settle_time: 0.7         # seconds to wait before/after each test move
cycles: 3                # test moves per pressure advance value

# Length of the high pass filter, as a multiple of the acceleration ramp
window_ratio: 1.5

# Pressure advance sweep
pa_start: 0.000
pa_end: 0.080
pa_step: 0.010
refine_passes: 1
refine_ratio: 0.25

# Load cell sampling
sample_rate: 100         # Hz (the MCU report rate is raised temporarily)
sensor_settle: 0.6      # s to wait after enabling the sensor (see below)
min_response_ratio: 5.0  # minimum force response / sensor noise
require_response: True   # abort when the load cell does not react at all

# Behaviour
# Staged config changes (pressure_advance, profiles, tool_profiles) are
# written to printer.cfg automatically when the printer is idle.  This runs
# Klipper's SAVE_CONFIG, so the printer restarts once.
auto_save_config: True
auto_save_delay: 1.0     # seconds to wait before the automatic save
# save_config: False     # legacy option; kept for old macros
restore_sensor_state: True
suspend_runout_sensors: True

# Pressure advance per filament type (see "Different pressure advance per
# filament type" below)
#profiles: PLA=0.0213, PETG=0.0245
#tool_profiles: 0=PLA, 1=PETG
auto_apply_profiles: True
# How often ACE is polled for a completed toolchange (seconds)
tool_poll_interval: 0.5
```

### Notes on the parameters

* `filament_speed` is the speed of the **filament** (not of the nozzle).
  `2.5 mm/s` is about `6 mm3/s` of melt flow, which is a realistic print
  flow for a 0.4 mm nozzle.  Larger values give a stronger signal but
  risk overrunning the hotend.
* `accel_ratio` is the toolhead acceleration divided by the toolhead speed.
  It defines the length of the acceleration ramp (`1 / accel_ratio`
  seconds).  A longer ramp is easier to sample but takes longer.
* `window_ratio` must be about `1.5`; it defines how much of the
  acceleration ramp is used for the high pass filter.  If the hotend is
  very slow (a long melt chamber) a larger value may help.
* `sample_rate` is the rate at which the MCU reports load cell readings.
  The plugin raises the rate of the `[cs1237]` section temporarily and
  restores it afterwards.  100 Hz uses about 9 % of the serial bandwidth
  of the `nozzle_mcu`.
* `sensor_settle` is the time the plugin waits after it enables the load
  cell before it starts measuring.  The CS1237 output swings wildly for
  roughly 150 ms after it is enabled (the amplifier has to settle) and
  those samples would otherwise poison the baseline.  The fork's own
  `probe_ks1` waits 500 ms for the same reason.
* Direct drive extruders normally need a PA between `0.005` and `0.08`;
  widen `pa_end` if the result ends up at the edge of the range.

## Commands

> All parameters use the `NAME=value` syntax (this is how Klipper parses
> extended commands).

### `AUTO_PRESSURE_ADVANCE_CALIBRATE` / `AUTO_PRESSURE_ADVANCE`
Runs the load cell based calibration.

```gcode
G28
AUTO_PRESSURE_ADVANCE_CALIBRATE EXTRUDER_TEMP=220 PA_START=0.0 PA_END=0.08 PA_STEP=0.01 PROFILE=PLA
```

`SAVE` defaults to `1`, so the result, the `profiles` list and any tool
mapping are staged and then written to `printer.cfg` automatically when the
printer is idle.  Use `SAVE=0` to try a value without persisting it.

Parameters: `PA_START`, `PA_END`, `PA_STEP`, `EXTRUDER_TEMP`, `BED_TEMP`,
`CYCLES`, `SAMPLE_RATE`, `EXTRUDER`, `SAVE`, `PROFILE`.  Older macros used
`PA_PROFILE=<name>`; it is accepted as an alias for `PROFILE`.

The output lists the score, the force response and the antisymmetry for
every measured pressure advance, plus the noise floor of the sensor and
the spread of the score.  A warning is printed when the best value is at
the edge of the tested range or when the differences between the measured
values are smaller than the sensor noise.

### `AUTO_PRESSURE_ADVANCE_TEST`

Runs a single test move and reports the measured values - use it to check
that the load cell reacts to extrusion before running a full sweep.

```gcode
AUTO_PRESSURE_ADVANCE_TEST
```

Parameters: `EXTRUDER_TEMP`.

### `AUTO_PRESSURE_ADVANCE_SET`

Sets the pressure advance by hand.  With `PROFILE=` the value is also stored
as a named filament profile.  `SAVE` defaults to `1`; both the live value and
the profile are automatically persisted to `printer.cfg` when the printer is
idle.

```gcode
AUTO_PRESSURE_ADVANCE_SET ADVANCE=0.035
AUTO_PRESSURE_ADVANCE_SET ADVANCE=0.0213 PROFILE=PLA
```

Parameters: `ADVANCE`, `SMOOTH_TIME`, `EXTRUDER`, `SAVE`, `PROFILE`.

### `AUTO_PRESSURE_ADVANCE_MAP`

Maps an ACE Pro tool number to a stored profile so toolchanges select it
automatically.

```gcode
AUTO_PRESSURE_ADVANCE_MAP TOOL=0 PROFILE=PLA
```

`SAVE` defaults to `1`, so the mapping is written to `printer.cfg`
automatically when the printer is idle.

### Automatic persistence

`SAVE_CONFIG` rewrites `printer.cfg` and restarts Klipper.  To avoid
interrupting a print, the plugin stages changes with `configfile.set()` and
runs `SAVE_CONFIG` from a timer after `auto_save_delay`.  It waits while
`print_stats.state` is `printing` or `paused`, while ACE reports a toolchange
in progress, and while a calibration is running.  `AUTO_PRESSURE_ADVANCE_STATUS`
shows `auto save : waiting to save (...)` while it is waiting.  If Klipper
rejects the save, run `SAVE_CONFIG` manually after fixing the reported problem.

### `AUTO_PRESSURE_ADVANCE_STATUS`

Reprints the plugin version, the configured sensor/extruder and the result
of the last calibration.  The version line is the quickest way to confirm
which build of the plugin the printer is actually running:

```
auto_pressure_advance plugin version 1.4
  sensor          : cs1237
  extruder        : extruder
  ace tool        : T0
  active profile  : pla
  auto save       : on
  unknown options : none
```

## Different pressure advance per filament type

### What Klipper supports natively

Klipper stores one `pressure_advance` per **extruder**:

* With several extruders (`[extruder]`, `[extruder1]`, ...) each section
  has its own `pressure_advance` and each tool gets its own value - no
  macros needed.
* With a **single** extruder plus an ACE Pro (as on the Kobra 3 Max)
  there is only one extruder, so there is only one pressure advance at
  any moment.  It can still be changed at runtime with
  `SET_PRESSURE_ADVANCE ADVANCE=<value>`, which is what this plugin
  uses.

### Is it worth it?

Pressure advance compensates the *filament travel delay* - the time the
filament needs to reach the melt chamber - plus the response of the
chamber itself.  For one printer and one hotend that delay is almost the
same for every filament; what really differs between filament types is
the **flow rate** (melt viscosity), and that belongs in the slicer's
extrusion multiplier, not in pressure advance.

Filament type still shifts the optimum a little (different viscosity and
melt temperature change the chamber's pressure response), and the
temperature matters more than the type.  On a direct drive extruder
where the pressure advance is small (around 0.02) the difference between
PLA and PETG is often only a few thousandths - possibly less than the
uncertainty of the measurement.

So: **measure it, compare it, and only then use separate values.**  If the
measured values for your filaments are within the noise of each other, one
value for all of them is the better choice.

### Measuring one value per filament type

The plugin measures the filament that is currently loaded, so run it once
per material - and at the temperature the material is printed at, because
temperature shifts the optimum as well:

```gcode
# PLA loaded, printed at 210 C
AUTO_PRESSURE_ADVANCE_CALIBRATE PROFILE=PLA EXTRUDER_TEMP=210
# PETG loaded, printed at 240 C
AUTO_PRESSURE_ADVANCE_CALIBRATE PROFILE=PETG EXTRUDER_TEMP=240
```

`PROFILE=<name>` stores the result under that name in the `profiles` option
of the `[auto_pressure_advance]` section.  With `auto_save_config: True` the
plugin stages the value and runs `SAVE_CONFIG` automatically once the printer
is idle; Klipper writes the values into the autosave block at the bottom of
`printer.cfg` and then restarts.

### Using the values

Map the ACE Pro tool index (`T0`, `T1`, ...) to a profile name:

```ini
[auto_pressure_advance]
profiles: PLA=0.0213, PETG=0.0245
tool_profiles: 0=PLA, 1=PETG
```

With `auto_apply_profiles: True` (the default) the plugin watches the
ACE Pro manager (`printer.ace`) and reads `current_index` from its
`get_status()` callback.  When ACE sets a new tool index, the plugin waits
for `toolchange_in_progress` to clear (i.e. for the post-toolchange purge to
finish) and then applies the mapped pressure advance.  A multi-material
print therefore uses the right value for each filament.  The application is
suspended while a calibration is running, and the current profile is
re-applied after a Klipper restart.

The mapping can also be edited without restarting:

```gcode
AUTO_PRESSURE_ADVANCE_MAP TOOL=0 PROFILE=PLA
```

The automatic save writes the updated `tool_profiles` value to
`printer.cfg` and restarts Klipper when it is safe to do so.

Manual control:

```gcode
AUTO_PRESSURE_ADVANCE_PROFILES    # list the stored profiles and active tool
AUTO_PRESSURE_ADVANCE_APPLY PROFILE=PETG
AUTO_PRESSURE_ADVANCE_STATUS      # version, active profile and last calibration
```

If you would rather not use this plugin for the switching, the same
thing can be done with a macro - the ACE Pro already runs
`_ACE_POST_TOOLCHANGE` after every filament change:

```ini
[gcode_macro _ACE_POST_TOOLCHANGE]
gcode:
    {% set pa = {0: 0.0213, 1: 0.0245} %}
    {% set tool = printer.ace.current_index|default(-1)|int %}
    {% if tool in pa %}
        SET_PRESSURE_ADVANCE ADVANCE={pa[tool]}
    {% endif %}
    ... your existing macro body ...
```

## Troubleshooting

### `Option 'extruder' is not valid in section 'auto_pressure_advance'`

Klipper refuses to start when a config option is **not read** by the
module that owns the section (`ConfigValidate.check_unused` in
`klippy/configfile.py`).  The message therefore means: *the module that
was loaded for `[auto_pressure_advance]` does not know the option
`extruder`*.

That is what happens when the printer is running an **older copy** of this
plugin (one written against a different option set) while the config file
already contains the newer options.

1. Copy the current `auto_pressure_advance.py` over the one on the printer
   (the file that is loaded is the one in the Klipper installation that
   actually runs, usually `~/klipper/klippy/extras/`).
2. `FIRMWARE_RESTART`
3. Run `AUTO_PRESSURE_ADVANCE_STATUS` and check that it reports
   `version 1.4` and the ACE tool/profile currently in use.

Version 1.4 also *consumes* options it does not recognise
(it logs a warning for each one and keeps going), so a config file that
still carries options from an older config block can no longer stop the
printer from starting.  The recognised options are listed above; remove
the obsolete ones from the config once the printer runs again.

### `Section 'auto_pressure_advance' is not a valid config section`

The plugin file is not in the Klipper installation that is running.  Copy
`auto_pressure_advance.py` into `~/klipper/klippy/extras/` and restart.

### The calibration does not find a clear minimum

See "Safety & tips" below - normally the sensor noise is too large
compared to the pressure advance transient.

## Safety & tips

* **Homing required.**  Run `G28` first; the plugin refuses to run
  otherwise.
* **Hot nozzle required.**  The plugin heats the nozzle to
  `extruder_temp` and waits for it.  The nozzle is left hot afterwards.
* **The test extrudes in the air.**  The filament droops - put a sheet of
  paper on the bed or lower `test_z` to about `0.2` to print the test
  onto the bed instead (then make sure the nozzle is at the right height
  first).
* **Do not run this during a print.**
* The plugin temporarily raises the load cell report rate and restores the
  previous setting (and the previous `enable` state of the sensor)
  afterwards.  The MCU trigger sensitivity is restored to the value from
  the `[cs1237]` section.
* If the score does not change much over the sweep, the measurement is
  dominated by noise.  Try more `CYCLES`, a larger `filament_speed`, a
  slower `move_speed` or a hotter nozzle.

## Limitations

* The result is a **starting point**.  Pressure advance also depends on
  the filament, the temperature and the printing speed, and the load cell
  only sees the part of the filament path that is mechanically coupled to
  the strain gauge.  Verify the result with a corner test (or Klipper's
  `TUNING_TOWER`) and adjust it if needed.
* The measurement describes the nozzle pressure of *this* hotend with
  *this* filament.  A different filament or a much different temperature
  can shift the optimum.
* The plugin can only measure pressure advance for the acceleration ratio
  it is run with.  The value that is optimal for a slow, gentle move is
  not necessarily the value that is optimal for a fast printing move.
* `smooth_time` is preserved as reported by the extruder and is not
  auto-tuned by this plugin.  Use `AUTO_PRESSURE_ADVANCE_SET
  SMOOTH_TIME=...` if needed.
