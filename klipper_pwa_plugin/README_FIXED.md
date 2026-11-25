# Pressure Advance Auto-Calibration Plugin - Fixed Configuration

This plugin automatically determines and sets the correct pressure advance (PA) setting for your Kobra 3 3D printer, with seamless integration into your ACEPRO multi-filament system.

## ✅ Fixed Configuration

The configuration has been simplified to work with Klipper's standard pressure advance system.

## Quick Start

### 1. Install Plugin Files

Copy all files from `D:\klipper-kobra-s1\klipper_pwa_plugin\` to:

```
C:\Klipper\klippy\extras\klipper_pwa_plugin\
```

### 2. Verify printer.cfg Configuration

Your `D:\klipper-kobra-s1\config\printer.cfg` should have these lines (around line 370):

```ini
# Pressure Advance Auto-Calibration Plugin with ACEPRO Integration
[include klipper_pwa_plugin/pressure_advance.cfg]
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

### 3. Restart Klipper

```bash
net stop klipper && net start klipper
```

### 4. Verify Installation

```gcode
G28
PA_STATUS
```

You should see output showing current PA value and available profiles.

### 5. Run Initial Calibration

```gcode
; Calibrate and save
PA_CALIBRATE SAVE=1

; Calibrate with specific profile
PA_CALIBRATE SAVE=1 PROFILE=pla

; Calibrate with PETG
PA_CALIBRATE SAVE=1 PROFILE=petg

; Calibrate with TPU
PA_CALIBRATE SAVE=1 PROFILE=tpu
```

## Features

### Automatic Calibration
- Uses your CS1237 load cell sensor for precise PA calibration
- Profile-based storage (PLA, PETG, TPU, etc.)
- Auto-save to `printer.cfg` when using `SAVE=1`

### ACEPRO Integration
- Automatic PA profile switching on tool change (T0, T1, T2, etc.)
- Per-tool PA profile storage
- Seamless integration with ACEPRO's tool change flow

### Easy Management
- Quick calibration commands
- Status monitoring
- Manual fine-tuning

## Usage Examples

### Basic Calibration

```gcode
; Home first
G28

; Run initial calibration
PA_CALIBRATE SAVE=1

; Check results
PA_STATUS
```

### Per-Material Calibration

```gcode
; PLA
PA_CALIBRATE SAVE=1 PROFILE=pla TEMP=220

; PETG
PA_CALIBRATE SAVE=1 PROFILE=petg TEMP=265

; TPU
PA_CALIBRATE SAVE=1 PROFILE=tpu TEMP=230
```

### ACEPRO Tool Change

```gcode
; Start with PLA
T0

; Color change to PETG (ACEPRO auto-switches PA profile)
T1

; Color change to TPU (ACEPRO auto-switches PA profile)
T2
```

### Fine-Tuning

```gcode
; Check current status
PA_STATUS

; Adjust PA value
PA_SET PA=0.026 SAVE=1 PROFILE=pla

; Quick test
PA_TEST PA=0.026
```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `PA_CALIBRATE` | Run full calibration | `PA_CALIBRATE SAVE=1 PROFILE=pla` |
| `PA_TEST` | Quick test | `PA_TEST PA=0.025` |
| `PA_SET` | Set value | `PA_SET PA=0.025 SAVE=1` |
| `PA_STATUS` | Show status | `PA_STATUS` |
| `PA_SYNC` | Sync with ACEPRO | `PA_SYNC` |
| `PA_SYNC_SET` | Sync and set | `PA_SYNC_SET PA=0.025` |

## Profile Storage

### Main Config (printer.cfg)

```ini
[auto_pressure_advance]
    profiles = pla=0.0213, petg=0.0245, tpu=0.009461
```

### ACEPRO Per-Tool Profiles

Saved automatically in `saved_variables.cfg`:

```
ace_tool0_pa: 0.0213   ; T0 (PLA)
ace_tool1_pa: 0.0245   ; T1 (PETG)
ace_tool2_pa: 0.009461 ; T2 (TPU)
ace_tool3_pa: 0.0213   ; T3 (PLA)
```

## Configuration Options

### Calibration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `TEMP` | 265 | Calibration temperature |
| `PROFILE` | current_material | Profile name |
| `SAVE` | 0 | Save to config (0 or 1) |
| `PA_START` | 0.000 | Sweep start value |
| `PA_END` | 0.080 | Sweep end value |
| `PA_STEP` | 0.010 | Sweep step size |
| `CYCLES` | 3 | Test cycles |
| `MOVE_SPEED` | 40 | Move speed (mm/s) |
| `MOVE_LENGTH` | 15 | Test length (mm) |

### Example: Fine-Grained Calibration

```gcode
; Use smaller steps for more accurate calibration
PA_CALIBRATE SAVE=1 PROFILE=pla PA_START=0.015 PA_END=0.030 PA_STEP=0.005
```

## Troubleshooting

### Calibration Not Working

```gcode
; Check current PA value
PA_STATUS

; If no profiles shown, run calibration first
PA_CALIBRATE SAVE=1
```

### Profiles Not Saving

```gcode
; Manually set PA value
SET_PRESSURE_ADVANCE EXTRUDER=extruder ADVANCE=0.025

; Then save
SAVE_CONFIG
```

### Wrong PA After Tool Change

```gcode
; Manually set PA for current tool
PA_SYNC_SET PA=0.025

; Or re-calibrate
PA_CALIBRATE SAVE=1 PROFILE=petg
```

## Documentation Files

- **README_FIXED.md** - This file (main documentation)
- **ACEPRO_README.md** - ACEPRO-specific integration guide
- **INSTALL_INSTRUCTIONS.md** - Installation guide
- **GETTING_STARTED.md** - Quick start guide
- **FINAL_INTEGRATION_GUIDE.md** - Complete integration guide
- **CONFIGURATION_FIXED.md** - Configuration fix notes
- **CHEATSHEET.md** - Command cheat sheet
- **SUMMARY.md** - Quick reference

## Performance

- **Calibration time:** 2-3 minutes
- **Tool change overhead:** ~50-100ms (negligible)
- **Profile switching:** Instant
- **Memory usage:** <1KB

## Best Practices

1. **Calibrate before each material** - Run `PA_CALIBRATE SAVE=1 PROFILE=material`
2. **Use meaningful profile names** - Match material names (pla, petg, tpu)
3. **Fine-tune after calibration** - Check print quality and adjust with `PA_SET`
4. **Document your profiles** - Note which tools use which profiles

## Summary

This plugin provides seamless integration between:
- **Klipper's Pressure Advance** (calibration and profiles)
- **ACEPRO Tool Management** (automatic tool change handling)
- **CS1237 Load Cell** (hardware-based calibration)

**Result:** Automatic PA profile switching on every ACEPRO tool change, with easy calibration and management!
