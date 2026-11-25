# Pressure Advance Auto-Calibration Plugin - Cheatsheet

## Quick Commands

```gcode
; Home first
G28

; Full calibration (recommended)
PA_CALIBRATE SAVE=1

; Calibrate with custom profile
PA_CALIBRATE SAVE=1 PROFILE=pla

; Quick test of current PA
PA_TEST

; Set specific PA value
PA_SET PA=0.025 SAVE=1

; Check status
PA_STATUS
```

## Common Calibration Scenarios

### First Time Setup
```gcode
G28
PA_CALIBRATE SAVE=1
```

### Changed Filament
```gcode
G28
PA_CALIBRATE SAVE=1 PROFILE=new_filament
```

### Optimizing for Specific Material
```gcode
; PLA
PA_CALIBRATE SAVE=1 PROFILE=pla TEMP=220

; PETG
PA_CALIBRATE SAVE=1 PROFILE=petg TEMP=265

; TPU
PA_CALIBRATE SAVE=1 PROFILE=tpu TEMP=230
```

### Fine-Tuning
```gcode
; Check current PA
PA_STATUS

; Adjust by small amounts
PA_SET PA=0.026 SAVE=1
PA_SET PA=0.027 SAVE=1
```

## Parameters Reference

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `TEMP` | 265 | 180-300 | Extruder temp for calibration |
| `PROFILE` | current_material | any string | Profile name |
| `SAVE` | 0 | 0 or 1 | Save to config |
| `PA_START` | 0.000 | 0.000-0.100 | Starting PA value |
| `PA_END` | 0.080 | 0.005-0.100 | Ending PA value |
| `PA_STEP` | 0.010 | 0.005-0.020 | Step size |
| `CYCLES` | 3 | 1-5 | Test cycles |
| `MOVE_SPEED` | 40 | 30-60 | Move speed (mm/s) |
| `MOVE_LENGTH` | 15 | 10-20 | Test length (mm) |

## Example Commands with Options

```gcode
; Fine-grained sweep
PA_CALIBRATE SAVE=1 PA_START=0.005 PA_END=0.060 PA_STEP=0.005

; Faster calibration
PA_CALIBRATE SAVE=1 MOVE_SPEED=60 CYCLES=2

; More accurate
PA_CALIBRATE SAVE=1 CYCLES=5 PA_STEP=0.005
```

## Profile Management

```gcode
; View available profiles
PA_STATUS

; Create new profile
PA_CALIBRATE SAVE=1 PROFILE=my_material

; Use specific profile
T0
PA_CALIBRATE SAVE=1 PROFILE=pla
T1
PA_CALIBRATE SAVE=1 PROFILE=petg
```

## Troubleshooting

### Calibration Fails
```gcode
; Check load cell sensor
PA_STATUS

; Verify auto_pressure_advance is loaded
M400

; Check extruder temp
M145 S0
M145 S1
```

### Wrong Results
```gcode
; Reset to zero and recalibrate
SET_PRESSURE_ADVANCE EXTRUDER=extruder ADVANCE=0.0
PA_CALIBRATE SAVE=1

; Try different sweep range
PA_CALIBRATE SAVE=1 PA_START=0.005 PA_END=0.060
```

### Save Not Working
```gcode
; Manually save
SET_PRESSURE_ADVANCE EXTRUDER=extruder ADVANCE=0.025
SAVE_CONFIG

; Check printer.cfg for new value
```

## Reading the Output

```
=== Pressure Advance Status ===
Current PA: 0.025
Nozzle Temp: 265.0C
Target Temp: 300.0C
Available Profiles:
  pla: 0.0213
  petg: 0.0245
  tpu: 0.009461
===============================
```

- **Current PA**: Currently active value
- **Nozzle Temp**: Current extruder temperature
- **Available Profiles**: Saved profiles with their PA values
- **==============================**: Separator line

## Typical PA Values

| Filament | Typical Range |
|----------|--------------|
| PLA | 0.015 - 0.025 |
| PETG | 0.020 - 0.030 |
| ABS | 0.020 - 0.030 |
| TPU | 0.005 - 0.015 |
| PVA | 0.010 - 0.020 |

## Installation Checklist

- [ ] Copy plugin to `C:\Klipper\klippy\extras\klipper_pwa_plugin\`
- [ ] Add `[include klipper_pwa_plugin/pressure_advance.cfg]` to printer.cfg
- [ ] Change `save_config: False` to `save_config: True` in `[auto_pressure_advance]`
- [ ] Restart Klipper
- [ ] Run `PA_STATUS` to verify installation
- [ ] Run `PA_CALIBRATE SAVE=1` for first calibration

## Documentation Files

- **README.md** - User documentation
- **INSTALLATION.md** - Installation guide
- **SUMMARY.md** - Quick reference
- **DIAGRAM.md** - Architecture overview
- **CONTRIBUTING.md** - Contribution guide
- **CHEATSHEET.md** - This file

## Related Commands

```gcode
; From auto_pressure_advance
AUTO_PRESSURE_ADVANCE_CALIBRATE
AUTO_PRESSURE_ADVANCE_PROFILES

; From Klipper
SET_PRESSURE_ADVANCE
M400
SAVE_CONFIG

; Home
G28
```
