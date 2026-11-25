# Final Configuration Fix Summary

## Issue Resolved

The error `"Option 'variables' is not valid in section 'gcode_macro pa_calibrate'"` has been fixed by:

1. **Removing the `variables:` block** from the `gcode_macro` sections (Klipper doesn't support this in the same way)
2. **Moving variable documentation** to the `description:` field as comments
3. **Keeping only essential `variables:` blocks** that Klipper accepts

## Fixed Files

### pressure_advance.cfg

**Before (line 16-27):**
```ini
[gcode_macro PA_CALIBRATE]
description: Calibrate pressure advance using load cell sensor
variables:
    TEMP: Extruder temperature for calibration (default: 265)
    PROFILE: Profile name for saving results (default: current_material)
    SAVE: Save to config (default: 0)
    ...
```

**After:**
```ini
[gcode_macro PA_CALIBRATE]
description: Calibrate pressure advance using load cell sensor
# Variables (for documentation purposes):
#   TEMP: Extruder temperature for calibration (default: 265)
#   PROFILE: Profile name for saving results (default: current_material)
#   SAVE: Save to config (default: 0)
#   ...
gcode:
    ...
```

### pressure_advance_acepro.cfg

**Complete rewrite** with proper Klipper macro syntax.

## Installation Steps

### 1. Copy Fixed Files to Klipper Extras

```powershell
# This has already been done, but to verify:
Copy-Item -Path "D:\klipper-kobra-s1\klipper_pwa_plugin\*.cfg" -Destination "C:\Klipper\klippy\extras\klipper_pwa_plugin\" -Force
```

### 2. Verify printer.cfg Includes

Your `D:\klipper-kobra-s1\config\printer.cfg` should have (around line 370):

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

### 5. Run Initial Calibration

```gcode
PA_CALIBRATE SAVE=1
```

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

### Quick Test

```gcode
; Quick test of current PA
PA_TEST

; Test with specific value
PA_TEST PA=0.025
```

### Set Specific Value

```gcode
; Set specific PA value
PA_SET PA=0.025 SAVE=1

; Set with profile
PA_SET PA=0.025 SAVE=1 PROFILE=pla
```

### Check Status

```gcode
PA_STATUS
```

### ACEPRO Tool Change

```gcode
; Just run the tool change command
T1

; ACEPRO automatically switches PA profile!
```

### Manual Sync

```gcode
; Sync PA with current tool
PA_SYNC

; Sync and set specific PA value
PA_SYNC_SET PA=0.025
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
| `PA_PROFILE` | Set profile | `PA_PROFILE PROFILE=pla` |

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

### If Klipper Still Has Issues

1. **Check the includes are correct:**
   ```bash
   Get-Content "D:\klipper-kobra-s1\config\printer.cfg" | Select-String "klipper_pwa_plugin"
   ```

2. **Verify plugin files exist in Klipper extras:**
   ```bash
   Get-ChildItem "C:\Klipper\klippy\extras\klipper_pwa_plugin" | Select-Object Name
   ```

3. **Check for syntax errors:**
   ```bash
   Get-Content "C:\Klipper\klippy\extras\klipper_pwa_plugin\pressure_advance.cfg" | Select-Object -First 30
   ```

4. **Restart Klipper:**
   ```bash
   net stop klipper && net start klipper
   ```

### Expected Output After Fix

After restarting and running `PA_STATUS`, you should see:

```
=== Pressure Advance Status ===
Current PA: 0.005939
Nozzle Temp: XX.XC
Target Temp: XXX.XC
Current ACE Tool: T-1
===============================
Note: ACEPRO will auto-switch PA profiles on tool change.
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
- **FINAL_FIX_SUMMARY.md** - This file

## Summary

✅ **Fixed `variables:` block** - Moved to comments in `description:` field
✅ **Simplified macro syntax** - Removed unsupported Klipper features
✅ **Updated plugin files** - Copied to Klipper extras directory
✅ **ACEPRO integration ready** - Automatic tool change PA switching
✅ **Ready for calibration** - Run `PA_CALIBRATE SAVE=1`

**Klipper should now start without errors!**
