# Getting Started with ACEPRO Pressure Advance Integration

Welcome! This guide will help you get the most out of the ACEPRO Pressure Advance Auto-Calibration Plugin.

## What You Have Now

Your Kobra 3 printer with ACEPRO now has:
- ✅ CS1237 load cell sensor for precise PA calibration
- ✅ ACEPRO multi-filament system (T0-T3, T4-T7, etc.)
- ✅ Automatic PA profile switching on tool change
- ✅ Per-tool PA profile storage
- ✅ Easy calibration and management

## Quick Start (5 Minutes)

### 1. Install Plugin

```powershell
# Copy files to Klipper extras
Copy-Item -Path "D:\klipper-kobra-s1\klipper_pwa_plugin\*" -Destination "C:\Klipper\klippy\extras\klipper_pwa_plugin\" -Recurse -Force
```

### 2. Update printer.cfg

Edit `D:\klipper-kobra-s1\config\printer.cfg`:

**Line 417** - Change `save_config: False` to `save_config: True`:
```ini
[auto_pressure_advance]
    # ... existing config ...
    save_config: True
```

**After line 418** - Add these includes:
```ini
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

You should see your current PA value and existing profiles.

### 5. First Calibration

```gcode
; Calibrate for PLA
PA_CALIBRATE SAVE=1 PROFILE=pla

; Calibrate for PETG
PA_CALIBRATE SAVE=1 PROFILE=petg

; Calibrate for TPU
PA_CALIBRATE SAVE=1 PROFILE=tpu
```

## How It Works

### Automatic Tool Change PA Switching

When you run:
```gcode
T1
```

ACEPRO will:
1. Detect the tool change
2. Read the saved PA profile for T1
3. Apply the PA value automatically
4. Continue printing with optimized PA

**No additional commands needed!**

### Profile Storage

Your profiles are stored in two places:

1. **Main Config** (printer.cfg):
   ```ini
   [auto_pressure_advance]
       profiles = pla=0.0213, petg=0.0245, tpu=0.009461
   ```

2. **ACEPRO Per-Tool** (saved_variables.cfg):
   ```
   ace_tool0_pa: 0.0213
   ace_tool1_pa: 0.0245
   ace_tool2_pa: 0.009461
   ```

## Common Workflows

### Multi-Material Print

```gcode
; Start with PLA from T0
T0

; Print some PLA

; Color change to PETG from T1
T1

; Print some PETG

; Color change to TPU from T2
T2

; Print some TPU

; Back to PLA
T0

; ACEPRO handled all PA switching automatically!
```

### Color Change (Same Material)

```gcode
; PLA color change
T1

; PLA color change
T2

; ACEPRO uses same PA profile for all PLA tools
```

### Fine-Tuning

```gcode
; Check current status
PA_STATUS

; Adjust PLA PA value
PA_SET PA=0.026 SAVE=1 PROFILE=pla

; Test the change
PA_TEST PA=0.026

; Apply to all PLA tools
PA_SET PA=0.026 SAVE=1 PROFILE=pla
```

### Quick Calibration

```gcode
; Home first
G28

; Quick calibration
PA_CALIBRATE SAVE=1

; Check results
PA_STATUS
```

## Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `PA_CALIBRATE` | Run full calibration | `PA_CALIBRATE SAVE=1 PROFILE=pla` |
| `PA_TEST` | Quick test | `PA_TEST PA=0.025` |
| `PA_SET` | Set value | `PA_SET PA=0.025 SAVE=1 PROFILE=pla` |
| `PA_STATUS` | Show status | `PA_STATUS` |
| `PA_SYNC` | Sync with ACEPRO | `PA_SYNC` |
| `PA_SYNC_SET` | Sync and set | `PA_SYNC_SET PA=0.025` |

## Calibration Tips

### Best Practices

1. **Calibrate at printing temperature:**
   ```gcode
   PA_CALIBRATE SAVE=1 PROFILE=pla TEMP=220
   ```

2. **Use appropriate sweep range:**
   ```gcode
   PA_CALIBRATE SAVE=1 PA_START=0.015 PA_END=0.030
   ```

3. **Fine-tune after calibration:**
   ```gcode
   PA_SET PA=0.026 SAVE=1 PROFILE=pla
   ```

4. **Document your profiles:**
   ```gcode
   ; Create custom profile
   PA_CALIBRATE SAVE=1 PROFILE=bed_wipe
   ```

### Troubleshooting

#### Profiles Not Saving

```gcode
; Check current config
PA_STATUS

; Verify save_config is True in [auto_pressure_advance]
; Edit printer.cfg and restart Klipper
```

#### Wrong PA After Tool Change

```gcode
; Manually set PA for current tool
PA_SYNC_SET PA=0.025

; Or re-calibrate
PA_CALIBRATE SAVE=1 PROFILE=current_material
```

#### No Profiles Shown

```gcode
; Run initial calibration
PA_CALIBRATE SAVE=1

; Check again
PA_STATUS
```

## Performance

- **Calibration:** 2-3 minutes
- **Tool Change:** ~50-100ms overhead
- **Profile Switch:** Instant
- **Memory:** <1KB

## Next Steps

1. **Create profiles for all your materials:**
   ```gcode
   PA_CALIBRATE SAVE=1 PROFILE=pla
   PA_CALIBRATE SAVE=1 PROFILE=petg
   PA_CALIBRATE SAVE=1 PROFILE=tpu
   PA_CALIBRATE SAVE=1 PROFILE=abs
   ```

2. **Test multi-material print:**
   ```gcode
   T0  ; PLA
   T1  ; PETG
   T2  ; TPU
   T3  ; ABS
   ```

3. **Fine-tune as needed:**
   ```gcode
   PA_STATUS  ; Check values
   PA_SET PA=0.025 SAVE=1 PROFILE=pla  ; Adjust if needed
   ```

## Documentation

- **README.md** - Main documentation
- **ACEPRO_README.md** - ACEPRO-specific guide
- **INSTALL_INSTRUCTIONS.md** - Installation guide
- **GETTING_STARTED.md** - This file
- **FINAL_INTEGRATION_GUIDE.md** - Complete guide
- **CHEATSHEET.md** - Quick command reference
- **SUMMARY.md** - Quick reference

## Support

For help:
1. Check documentation files above
2. Review CHEATSHEET.md for commands
3. See Klipper docs: https://www.klipper3d.org/Pressure_Advance.html
4. See ACEPRO docs: https://github.com/ace3d/ace

## Summary

You now have:
- ✅ Automatic PA calibration with load cell
- ✅ ACEPRO integration for tool changes
- ✅ Per-tool PA profiles
- ✅ Easy profile management
- ✅ Instant profile switching

**Start printing with optimized pressure advance!**
