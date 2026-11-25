# Klipper Pressure Advance Auto-Calibration Plugin

This plugin automatically determines and sets the correct pressure advance (PA) setting for your 3D printer using a load cell sensor (CS1237 or similar).

## Installation

1. Copy the plugin files to your Klipper `klippy/extras/` directory:
   ```
   klipper_pwa_plugin/
   ├── __init__.py
   ├── pressure_advance_auto_calibrate.py
   ├── pressure_advance.cfg
   └── README.md
   ```

2. Add to your `printer.cfg`:
   ```ini
   [include /path/to/klipper/extras/klipper_pwa_plugin/pressure_advance.cfg]
   ```

   **Note:** Your current setup already includes `auto_pressure_advance`, so just change `save_config: False` to `save_config: True` (which we've done for you).

## Usage

### Full Calibration (Recommended)

```gcode
; Home first
G28

; Run full calibration and save automatically
PA_CALIBRATE SAVE=1
```

**Options:**
- `TEMP=<temp>` - Extruder temperature (default: 265°C)
- `PROFILE=<name>` - Profile name for saving (default: current_material)
- `PA_START=<value>` - Starting PA value (default: 0.000)
- `PA_END=<value>` - Ending PA value for sweep (default: 0.080)
- `PA_STEP=<value>` - Step size for sweep (default: 0.010)
- `CYCLES=<n>` - Number of test cycles (default: 3)
- `MOVE_SPEED=<speed>` - Move speed for test (default: 40 mm/s)
- `MOVE_LENGTH=<length>` - Test move length (default: 15 mm)

### Quick Calibration

```gcode
; Calibrate and save with custom profile name
PA_CALIBRATE SAVE=1 PROFILE=pla
```

### Set Specific PA Value

```gcode
; Manually set and save a specific PA value
PA_SET PA=0.025 SAVE=1
```

### Quick Test

```gcode
; Quick test of current PA value (no sweep)
PA_TEST
```

```gcode
; Quick test with specific PA value
PA_TEST PA=0.025
```

### Check Status

```gcode
; Show current PA status and available profiles
PA_STATUS
```

## How It Works

1. **Homes** all axes and parks to test position
2. **Heats** extruder to calibration temperature
3. **Runs** a PA sweep using the load cell sensor to find optimal value
4. **Applies** the best PA value
5. **Saves** the result to `printer.cfg` automatically (when `SAVE=1`)

## Calibration Temperature

The default calibration temperature is 265°C. You can adjust this based on your typical printing temperature:
- PLA: ~220°C
- PETG: ~265°C
- ABS: ~250°C
- TPU: ~230°C

## Tips

1. **Run calibration** after changing filament types
2. **Use SAVE=1** to automatically save the result
3. **Check extrusion quality** - the calibration minimizes ringing but verify visually
4. **Store results** in profiles (e.g., `PROFILE=pla`, `PROFILE=petg`, `PROFILE=tpu`)

## Troubleshooting

- **No load cell?** Make sure `auto_pressure_advance` is configured in your `printer.cfg`
- **Calibration fails?** Check that your load cell sensor is working and connected
- **Wrong results?** Adjust `PA_START`, `PA_END`, or `PA_STEP` parameters

## Current Setup

Your Kobra 3 printer already has `auto_pressure_advance` configured with a CS1237 load cell. The plugin integrates seamlessly with this existing setup.
