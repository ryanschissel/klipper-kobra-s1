# Installation Instructions

## Quick Installation (3 Steps)

### Step 1: Copy Plugin Files

Copy all files from `D:\klipper-kobra-s1\klipper_pwa_plugin\` to:

```
C:\Klipper\klippy\extras\klipper_pwa_plugin\
```

Or use the PowerShell installer:
```powershell
cd D:\klipper-kobra-s1\klipper_pwa_plugin
.\install.ps1
```

### Step 2: Update printer.cfg

Edit `D:\klipper-kobra-s1\config\printer.cfg`:

**Change line 417** in the `[auto_pressure_advance]` section:

```ini
# Old line 417:
# Do not write the result to printer.cfg automatically
save_config: False

# New line 417:
# Do write the result to printer.cfg automatically after calibration
save_config: True
```

**Add these include lines** after your `[auto_pressure_advance]` section (around line 418):

```ini
[include klipper_pwa_plugin/pressure_advance.cfg]
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

### Step 3: Restart Klipper

```bash
net stop klipper && net start klipper
```

## Verification

After restarting, run:

```gcode
G28
PA_STATUS
```

You should see output like:

```
=== Pressure Advance Status ===
Current PA: 0.005939
Nozzle Temp: XX.XC
Target Temp: XXX.XC
Current ACE Tool: T-1
Available Profiles:
  petg: 0.0245
  pla: 0.0213
  tpu: 0.009461
===============================
Note: ACEPRO will auto-switch PA profiles on tool change.
```

## First Calibration

```gcode
; Home first
G28

; Run initial calibration
PA_CALIBRATE SAVE=1

; Check results
PA_STATUS
```

## What's Included

After installation, you'll have:

### G-code Macros

- `PA_CALIBRATE` - Run full calibration
- `PA_TEST` - Quick test of PA value
- `PA_SET` - Set specific PA value
- `PA_STATUS` - Show current PA status
- `PA_SYNC` - Sync with ACEPRO tool
- `PA_SYNC_SET` - Sync and set PA value
- `PA_PROFILE` - Set profile for material

### ACEPRO Integration

- Automatic PA profile switching on tool change
- Per-tool PA profile storage
- Seamless integration with ACEPRO's tool change flow

### Documentation

- README.md - Main documentation
- ACEPRO_README.md - ACEPRO-specific guide
- INSTALLATION.md - This file
- SUMMARY.md - Quick reference
- FINAL_INTEGRATION_GUIDE.md - Complete guide
- CHEATSHEET.md - Command cheat sheet
- QUICK_REFERENCE.md - Quick one-liners
- PROJECT_SUMMARY.md - Project overview

## Files to Copy

```
klipper_pwa_plugin/
├── __init__.py
├── setup.py
├── install.ps1
├── pressure_advance.cfg
├── pressure_advance_acepro.cfg
├── pressure_advance_auto_calibrate.py
├── pressure_advance_acepro.py
├── README.md
├── ACEPRO_README.md
├── INSTALLATION.md
├── SUMMARY.md
├── FINAL_INTEGRATION_GUIDE.md
├── CHEATSHEET.md
├── QUICK_REFERENCE.md
└── PROJECT_SUMMARY.md
```

## Manual Installation (if install.ps1 fails)

If the PowerShell installer doesn't work, manually copy these files:

### Core Files (Required)
```
__init__.py
pressure_advance.cfg
pressure_advance_acepro.cfg
pressure_advance_auto_calibrate.py
pressure_advance_acepro.py
```

### Documentation Files (Recommended)
```
README.md
ACEPRO_README.md
INSTALLATION.md
SUMMARY.md
FINAL_INTEGRATION_GUIDE.md
CHEATSHEET.md
QUICK_REFERENCE.md
PROJECT_SUMMARY.md
```

### Optional Files
```
setup.py
install.ps1
```

## Configuration

Your `printer.cfg` should look like this:

```ini
# ... existing config ...

[auto_pressure_advance]
    auto_apply_profiles: True
    sensor: cs1237
    extruder: extruder
    test_x: 210
    test_y: 210
    test_z: 25
    extruder_temp: 265
    filament_speed: 2.5
    accel_ratio: 10.0
    move_speed: 40.0
    move_length: 15.0
    prime_length: 5.0
    settle_time: 0.7
    cycles: 3
    window_ratio: 1.5
    pa_start: 0.000
    pa_end: 0.080
    pa_step: 0.010
    refine_passes: 1
    refine_ratio: 0.25
    sample_rate: 100
    sensor_settle: 0.6
    min_response_ratio: 5.0
    require_response: True
    save_config: True  # <-- Changed from False to True

[include klipper_pwa_plugin/pressure_advance.cfg]  # <-- Add this
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]  # <-- Add this

# ... rest of config ...
```

## Usage Examples

### Basic Calibration
```gcode
G28
PA_CALIBRATE SAVE=1
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

### Check Status
```gcode
PA_STATUS
```

### ACEPRO Tool Change (Automatic!)
```gcode
; Just run the tool change command
T1
; ACEPRO will automatically switch PA profile!
```

### Fine-Tuning
```gcode
; Adjust PA value
PA_SET PA=0.026 SAVE=1 PROFILE=pla

; Quick test
PA_TEST PA=0.026
```

## Troubleshooting

### "save_config: True" not working

1. Verify the line number in printer.cfg (should be around line 417)
2. Make sure you're editing the `[auto_pressure_advance]` section
3. Restart Klipper after changing

### No profiles shown in PA_STATUS

1. Run `PA_CALIBRATE SAVE=1` first
2. Check that `save_config: True` is set
3. Verify Klipper restarted after config change

### Profiles not switching on tool change

1. Check ACEPRO is working: `ACE_GET_STATUS`
2. Verify per-tool profiles exist in saved_variables
3. Run `PA_STATUS` to see current state

### Calibration fails

1. Make sure load cell sensor is connected
2. Verify `auto_pressure_advance` section is in printer.cfg
3. Check that extruder is heated before calibration

## Next Steps

After installation and first calibration:

1. **Create profiles for your materials:**
   ```gcode
   PA_CALIBRATE SAVE=1 PROFILE=pla
   PA_CALIBRATE SAVE=1 PROFILE=petg
   PA_CALIBRATE SAVE=1 PROFILE=tpu
   ```

2. **Test tool changes:**
   ```gcode
   T0  ; Should use PLA PA profile
   T1  ; Should use PETG PA profile
   T2  ; Should use TPU PA profile
   ```

3. **Fine-tune if needed:**
   ```gcode
   PA_STATUS  ; Check current values
   PA_SET PA=0.025 SAVE=1 PROFILE=pla  ; Adjust if needed
   ```

4. **Reference documentation:**
   - See README.md for full documentation
   - See CHEATSHEET.md for quick commands
   - See ACEPRO_README.md for ACEPRO-specific info

## Support Resources

- **Main Documentation:** README.md
- **ACEPRO Guide:** ACEPRO_README.md
- **Quick Reference:** SUMMARY.md
- **Command Cheat Sheet:** CHEATSHEET.md
- **Klipper Docs:** https://www.klipper3d.org/Pressure_Advance.html
- **ACEPRO Docs:** https://github.com/ace3d/ace

## Summary

After installation:

✅ Plugin files copied to Klipper extras
✅ printer.cfg updated with includes
✅ Klipper restarted
✅ Initial calibration run
✅ ACEPRO integration active
✅ Automatic PA switching on tool change

**You're ready to print with optimized pressure advance!**
