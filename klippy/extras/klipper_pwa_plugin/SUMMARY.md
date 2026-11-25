# Pressure Advance Auto-Calibration Plugin - Summary

## What This Plugin Does

This plugin automatically determines the optimal pressure advance (PA) setting for your 3D printer using your existing CS1237 load cell sensor. It integrates with your Klipper installation to:

1. **Automatically calibrate** PA values using sweep testing
2. **Save results** directly to your `printer.cfg` file
3. **Create profiles** for different filament types (PLA, PETG, TPU, etc.)
4. **Provide quick commands** for testing and adjusting PA values

## Files Created

```
klipper_pwa_plugin/
├── __init__.py              # Plugin initialization
├── pressure_advance_auto_calibrate.py  # Python G-code macros
├── pressure_advance.cfg     # Klipper G-code configuration
├── README.md                # User documentation
├── INSTALLATION.md          # Installation guide
└── SUMMARY.md               # This file
```

## Changes Made to Your Printer

### Updated `config/printer.cfg`
Changed line 417 in the `[auto_pressure_advance]` section:
```ini
# Do not write the result to printer.cfg automatically
save_config: False
```
to:
```ini
# Do write the result to printer.cfg automatically after calibration
save_config: True
```

## Quick Start

### Step 1: Copy to Klipper
Copy the `klipper_pwa_plugin` folder to:
```
C:\Klipper\klippy\extras\klipper_pwa_plugin\
```

### Step 2: Restart Klipper
In your Klipper terminal:
```bash
systemctl restart klippy          # Linux
# or
net stop klipper && net start klipper   # Windows
```

### Step 3: Run Calibration
```gcode
; Home first
G28

; Calibrate and save
PA_CALIBRATE SAVE=1
```

### Step 4: Check Results
```gcode
PA_STATUS
```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `PA_CALIBRATE` | Run full calibration | `PA_CALIBRATE SAVE=1` |
| `PA_CALIBRATE PROFILE=...` | Calibrate with profile name | `PA_CALIBRATE SAVE=1 PROFILE=pla` |
| `PA_SET PA=... SAVE=1` | Set and save specific value | `PA_SET PA=0.025 SAVE=1` |
| `PA_TEST` | Quick test of current PA | `PA_TEST PA=0.025` |
| `PA_STATUS` | Show current PA status | `PA_STATUS` |

## Calibration Parameters

- `TEMP` - Extruder temperature (default: 265°C)
- `PROFILE` - Profile name (default: current_material)
- `SAVE` - Save to config (default: 0, use 1 to save)
- `PA_START` - Starting PA value (default: 0.000)
- `PA_END` - Ending PA value (default: 0.080)
- `PA_STEP` - Step size (default: 0.010)
- `CYCLES` - Test cycles (default: 3)
- `MOVE_SPEED` - Move speed (default: 40 mm/s)
- `MOVE_LENGTH` - Test length (default: 15 mm)

## How It Works

The plugin uses your existing `auto_pressure_advance` hardware and performs:

1. **Home** all axes and park at test position
2. **Heat** extruder to calibration temperature
3. **Sweep** PA values from PA_START to PA_END
4. **Measure** filament response using load cell
5. **Calculate** optimal PA value
6. **Apply** the best value
7. **Save** to printer.cfg (when SAVE=1)

## Your Current Setup

Your Kobra 3 printer already has:
- CS1237 load cell sensor configured
- `auto_pressure_advance` section in printer.cfg
- Existing PA profiles (petg, pla, tpu)

The plugin enhances this by making calibration automatic and profile-based.

## Tips

- Run calibration after changing filament types
- Use different PROFILE names for different materials
- Check extrusion quality after calibration
- Store results in multiple profiles for different materials

## Support

For issues or questions, check:
- `klipper_pwa_plugin/README.md` - User documentation
- `klipper_pwa_plugin/INSTALLATION.md` - Installation guide
- Klipper documentation: https://www.klipper3d.org/Pressure_Advance.html
