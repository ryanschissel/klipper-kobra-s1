# Pressure Advance Auto-Calibration Plugin - Setup Complete

## ✅ Plugin is Ready to Use

Your Klipper Pressure Advance Auto-Calibration Plugin has been successfully set up and configured for use with your ACEPRO system.

## Current Status

### Plugin Files
- **Local source:** `D:\klipper-kobra-s1\klipper_pwa_plugin\`
- **Klipper extras:** `C:\Klipper\klippy\extras\klipper_pwa_plugin\`

### Included Macros
- `PA_CALIBRATE` - Run full PA calibration
- `PA_TEST` - Quick test of current PA value
- `PA_SET` - Set specific PA value
- `PA_STATUS` - Show current PA status
- `PA_SYNC` - Sync with ACEPRO tool
- `PA_SYNC_SET` - Sync and set PA value

### printer.cfg Configuration
Lines 370-372 include the plugin:
```ini
# Pressure Advance Auto-Calibration Plugin with ACEPRO Integration
[include klipper_pwa_plugin/pressure_advance.cfg]
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

## Next Steps

### 1. Restart Klipper

```bash
net stop klipper && net start klipper
```

### 2. Verify Installation

After restart, home and check status:

```gcode
G28
PA_STATUS
```

Expected output:
```
=== Pressure Advance Status ===
Current PA: 0.005939
Nozzle Temp: XX.XC
Target Temp: XXX.XC
Current ACE Tool: T-1
===============================
Note: ACEPRO will auto-switch PA profiles on tool change.
```

### 3. Run Initial Calibration

```gcode
; Home first
G28

; Run initial calibration
PA_CALIBRATE SAVE=1
```

### 4. Calibrate with Profiles

```gcode
; PLA
PA_CALIBRATE SAVE=1 PROFILE=pla

; PETG
PA_CALIBRATE SAVE=1 PROFILE=petg

; TPU
PA_CALIBRATE SAVE=1 PROFILE=tpu
```

## All Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `PA_CALIBRATE` | Run full calibration | `PA_CALIBRATE SAVE=1 PROFILE=pla` |
| `PA_TEST` | Quick test | `PA_TEST PA=0.025` |
| `PA_SET` | Set value | `PA_SET PA=0.025 SAVE=1` |
| `PA_STATUS` | Show status | `PA_STATUS` |
| `PA_SYNC` | Sync with ACEPRO | `PA_SYNC` |
| `PA_SYNC_SET` | Sync and set | `PA_SYNC_SET PA=0.025` |

## Usage Examples

### Basic Calibration

```gcode
; Home first
G28

; Run initial calibration
PA_CALIBRATE SAVE=1

; Calibrate with specific profile
PA_CALIBRATE SAVE=1 PROFILE=pla

; Calibrate with PETG
PA_CALIBRATE SAVE=1 PROFILE=petg

; Calibrate with TPU
PA_CALIBRATE SAVE=1 PROFILE=tpu
```

### ACEPRO Tool Change

```gcode
; Just run the tool change command
T1

; ACEPRO automatically switches PA profile!
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

## Documentation

All documentation is available in:
```
D:\klipper-kobra-s1\klipper_pwa_plugin\
```

Key files:
- **README_FIXED.md** - Main user documentation
- **ACEPRO_README.md** - ACEPRO-specific guide
- **INSTALL_INSTRUCTIONS.md** - Installation guide
- **GETTING_STARTED.md** - Quick start guide
- **SETUP_COMPLETE.md** - This file

## Summary

✅ **Plugin installed** - Files in Klipper extras directory
✅ **Configured correctly** - printer.cfg includes the plugin
✅ **Macros ready** - PA_CALIBRATE, PA_TEST, PA_SET, PA_STATUS, PA_SYNC, PA_SYNC_SET
✅ **ACEPRO integrated** - Automatic PA profile switching on tool change
✅ **Ready to use** - Run `PA_CALIBRATE SAVE=1` to calibrate

**Restart Klipper to complete the setup!**
