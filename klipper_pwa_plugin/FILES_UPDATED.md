# Files Updated - Pressure Advance Auto-Calibration Plugin

## Updated Files

### 1. pressure_advance.cfg

**Location:** `D:\klipper-kobra-s1\klipper_pwa_plugin\pressure_advance.cfg`

**Copied to:** `C:\Klipper\klippy\extras\klipper_pwa_plugin\pressure_advance.cfg`

**Contains:**
- `PA_CALIBRATE` - Run full calibration
- `PA_TEST` - Quick test of PA value
- `PA_SET` - Set specific PA value
- `PA_STATUS` - Show current PA status

**Fixed:**
- Removed Python f-strings (changed to Jinja2-compatible syntax)
- Fixed closing parentheses
- Removed `variables:` blocks

### 2. pressure_advance_acepro.py

**Location:** `D:\klipper-kobra-s1\klipper_pwa_plugin\pressure_advance_acepro.py`

**Copied to:** `C:\Klipper\klippy\extras\klipper_pwa_plugin\pressure_advance_acepro.py`

**Contains:**
- `PA_SYNC` - Synchronize with ACEPRO tool
- `PA_SYNC_SET` - Sync and set PA value
- `PA_PROFILE` - Set profile for material

**Fixed:**
- Removed Python f-strings (changed to Jinja2-compatible syntax)
- Removed extra closing parenthesis

### 3. pressure_advance_acepro.cfg

**Location:** `D:\klipper-kobra-s1\klipper_pwa_plugin\pressure_advance_acepro.cfg`

**Copied to:** `C:\Klipper\klippy\extras\klipper_pwa_plugin\pressure_advance_acepro.cfg`

**Contains:**
- `PA_SYNC` - Synchronize with ACEPRO tool
- `PA_SYNC_SET` - Sync and set PA value

**Fixed:**
- Removed Python f-strings (changed to Jinja2-compatible syntax)
- Removed problematic `PA_PROFILE` macro

## Configuration in printer.cfg

Your `D:\klipper-kobra-s1\config\printer.cfg` should have (around line 370-375):

```ini
# Pressure Advance Auto-Calibration Plugin with ACEPRO Integration
[auto_pressure_advance]
save_config: True

[include klipper_pwa_plugin/pressure_advance.cfg]
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

## How It Works

1. **`[auto_pressure_advance]` section** - Tells Klipper to use the hardware plugin for load cell calibration
2. **`[include ...]` statements** - Load the G-code macros from the plugin
3. **`.py` files** - Auto-loaded by Klipper from `klippy/extras/` directory

## Next Steps

### 1. Restart Klipper

```bash
net stop klipper && net start klipper
```

### 2. Verify Installation

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

### 3. Run Calibration

```gcode
PA_CALIBRATE SAVE=1
```

## Summary

✅ **All files updated** - Fixed Python f-strings and syntax issues
✅ **Files copied to Klipper extras** - Ready for use
✅ **printer.cfg configured** - Includes the plugin
✅ **auto_pressure_advance section present** - Required by Klipper

**Restart Klipper to complete the setup!**
