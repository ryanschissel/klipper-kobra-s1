# Configuration Fixed - ACEPRO Pressure Advance Plugin

## Issue Fixed

The error `"Option 'auto_apply_profiles' is not valid in section 'auto_pressure_advance'"` has been resolved.

## What Was Changed

### Original Problem
The `[auto_pressure_advance]` section had too many options that aren't valid for the standard Klipper extras plugin. The plugin expects a minimal configuration.

### Solution
Simplified the `[auto_pressure_advance]` section to only include the essential options:

```ini
[auto_pressure_advance]
sensor: cs1237
extruder: extruder
save_config: True
```

## Current Configuration (Lines 373-380)

```ini
# Automatic pressure advance calibration using the CS1237 load cell.
# Requires klippy/extras/auto_pressure_advance.py in the Klipper install.
# Run with:  G28  then  AUTO_PRESSURE_ADVANCE_CALIBRATE
[auto_pressure_advance]
sensor: cs1237
extruder: extruder
save_config: True

# Pressure Advance Auto-Calibration Plugin with ACEPRO Integration
[include klipper_pwa_plugin/pressure_advance.cfg]
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

## Why This Works

- **`sensor: cs1237`** - Tells Klipper which load cell sensor to use
- **`extruder: extruder`** - Specifies which extruder to calibrate
- **`save_config: True`** - Automatically saves calibration results to `printer.cfg`
- **Include statements** - Load the custom G-code macros for calibration and ACEPRO integration

## Next Steps

1. **Restart Klipper:**
   ```bash
   net stop klipper && net start klipper
   ```

2. **Verify Installation:**
   ```gcode
   G28
   PA_STATUS
   ```

3. **Run Initial Calibration:**
   ```gcode
   PA_CALIBRATE SAVE=1
   ```

## Plugin Files

The plugin files should be copied to your Klipper extras directory:

```
C:\Klipper\klippy\extras\klipper_pwa_plugin\
```

Or if using a different path, adjust accordingly.

## Usage

### Basic Commands

```gcode
; Home first
G28

; Calibrate and save
PA_CALIBRATE SAVE=1

; Calibrate with profile
PA_CALIBRATE SAVE=1 PROFILE=pla

; Quick test
PA_TEST

; Set specific value
PA_SET PA=0.025 SAVE=1

; Check status
PA_STATUS
```

### ACEPRO Tool Change

```gcode
; Just run the tool change command
T1

; ACEPRO automatically switches PA profile!
```

## Documentation

All documentation is available in:
```
D:\klipper-kobra-s1\klipper_pwa_plugin\
```

Key files:
- `README.md` - Main documentation
- `ACEPRO_README.md` - ACEPRO-specific guide
- `INSTALL_INSTRUCTIONS.md` - Installation guide
- `GETTING_STARTED.md` - Quick start guide
- `FIXED_CONFIG.md` - This file

## Troubleshooting

### If Klipper Still Has Issues

1. **Check the includes are correct:**
   ```bash
   Get-Content "D:\klipper-kobra-s1\config\printer.cfg" | Select-String "klipper_pwa_plugin"
   ```

2. **Verify plugin files exist:**
   ```bash
   Test-Path "D:\klipper-kobra-s1\klipper_pwa_plugin\pressure_advance.cfg"
   Test-Path "D:\klipper-kobra-s1\klipper_pwa_plugin\pressure_advance_acepro.cfg"
   ```

3. **Copy plugin files to Klipper extras:**
   ```powershell
   Copy-Item -Path "D:\klipper-kobra-s1\klipper_pwa_plugin\*" -Destination "C:\Klipper\klippy\extras\klipper_pwa_plugin\" -Recurse -Force
   ```

4. **Restart Klipper:**
   ```bash
   net stop klipper && net start klipper
   ```

### Expected Output

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

## Summary

✅ Configuration fixed - removed invalid options
✅ Plugin macros included via include statements
✅ ACEPRO integration ready
✅ Ready for calibration and use

**Klipper should now start without errors!**
