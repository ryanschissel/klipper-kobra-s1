# Fix printer.cfg for Pressure Advance Plugin

## Problem

The error `"Section 'auto_pressure_advance' is not a valid config section"` means Klipper doesn't recognize the `auto_pressure_advance` section.

## Solution

The `auto_pressure_advance` section in your `printer.cfg` is in the SAVE_CONFIG block (auto-generated section at the end of the file). We need to either:

1. **Option 1: Remove the includes and let the plugin handle profiles**
2. **Option 2: Add a minimal `auto_pressure_advance` section**

### Option 1: Remove Includes (Recommended)

Edit `D:\klipper-kobra-s1\config\printer.cfg` and find these lines (around line 371-372):

```ini
# Pressure Advance Auto-Calibration Plugin with ACEPRO Integration
[include klipper_pwa_plugin/pressure_advance.cfg]
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

**Remove or comment them out:**

```ini
# Pressure Advance Auto-Calibration Plugin with ACEPRO Integration
# [include klipper_pwa_plugin/pressure_advance.cfg]
# [include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

### Option 2: Add Minimal auto_pressure_advance Section

Add this section **before** the includes (around line 370):

```ini
[auto_pressure_advance]
save_config: True
```

Then keep the includes below it.

## Quick Fix Commands

### Step 1: Backup your current config

```powershell
Copy-Item "D:\klipper-kobra-s1\config\printer.cfg" "D:\klipper-kobra-s1\config\printer.cfg.backup"
```

### Step 2: Edit printer.cfg

Open `D:\klipper-kobra-s1\config\printer.cfg` in a text editor and:

1. **Find the `[auto_pressure_advance]` section** (it's commented out with `#*#`)
2. **Add a new `[auto_pressure_advance]` section** before the includes:

```ini
# Pressure Advance Auto-Calibration Plugin with ACEPRO Integration
[auto_pressure_advance]
save_config: True

[include klipper_pwa_plugin/pressure_advance.cfg]
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

### Step 3: Restart Klipper

```bash
net stop klipper && net start klipper
```

### Step 4: Verify Installation

```gcode
G28
PA_STATUS
```

## Expected Output

After restart, you should see:

```
=== Pressure Advance Status ===
Current PA: 0.005939
Nozzle Temp: XX.XC
Target Temp: XXX.XC
Current ACE Tool: T-1
===============================
Note: ACEPRO will auto-switch PA profiles on tool change.
```

## Alternative: Use Only Includes

If you want to use only the plugin macros without the hardware plugin:

```ini
# Pressure Advance Auto-Calibration Plugin with ACEPRO Integration
[auto_pressure_advance]
save_config: True

[include klipper_pwa_plugin/pressure_advance.cfg]
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

## Summary

The key is to have a minimal `[auto_pressure_advance]` section with just `save_config: True` before the plugin includes.

This tells Klipper to use the plugin macros for calibration while keeping the hardware plugin section minimal.
