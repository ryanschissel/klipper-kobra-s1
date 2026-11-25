# Pressure Advance Auto-Calibration - Quick Reference

## One-Liners

```gcode
; Home and calibrate
G28 PA_CALIBRATE SAVE=1

; Calibrate with profile
G28 PA_CALIBRATE SAVE=1 PROFILE=pla

; Check status
PA_STATUS

; Quick test
PA_TEST
```

## Before You Start

1. **Home** your printer: `G28`
2. **Make sure filament is loaded**
3. **Verify load cell is connected** (check `PA_STATUS` first)

## Common Workflows

### New Filament Type
```gcode
G28
PA_CALIBRATE SAVE=1 PROFILE=nylon
```

### After Printer Restart
```gcode
G28
PA_CALIBRATE SAVE=1
```

### Fine-Tune Existing Profile
```gcode
PA_STATUS
; See current value, then adjust:
PA_SET PA=0.026 SAVE=1
```

## Status Output

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

**What to look for:**
- `Current PA` - Currently active value
- `Available Profiles` - Your saved profiles
- If no profiles shown - run calibration first

## Quick Fixes

### Calibration Not Saving
```gcode
; Add SAVE=1 parameter
PA_CALIBRATE SAVE=1 PROFILE=pla
```

### Wrong Temperature
```gcode
; Specify your material temp
PA_CALIBRATE SAVE=1 PROFILE=pla TEMP=220
```

### Need Finer Sweep
```gcode
; Use smaller steps
PA_CALIBRATE SAVE=1 PA_STEP=0.005 CYCLES=5
```

## Installation Commands

```bash
; PowerShell
.\install.ps1

; Or manually copy to:
C:\Klipper\klippy\extras\klipper_pwa_plugin\
```

Then add to printer.cfg:
```ini
[include C:\Klipper\klippy\extras\klipper_pwa_plugin\pressure_advance.cfg]
```

## Tips

- **Run calibration** when extruder is cool (room temp)
- **Use SAVE=1** to automatically save results
- **Create profiles** for each filament type
- **Check print quality** after calibration
- **Restart Klipper** after changing profiles

## When to Calibrate

✓ Changed filament type
✓ After printer maintenance
✓ For new print jobs
✓ When print quality issues appear
✓ After printer upgrade

## When NOT to Calibrate

✗ Mid-print (save current print first)
✗ Extruder not at temp
✗ Load cell disconnected
✗ Filament not loaded

## Related Files

- `pressure_advance.cfg` - Main config
- `pressure_advance_auto_calibrate.py` - Python macros
- `README.md` - Full documentation
- `CHEATSHEET.md` - Quick commands
- `INSTALLATION.md` - Setup guide
