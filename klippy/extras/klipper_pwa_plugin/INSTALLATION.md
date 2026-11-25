# Installation Instructions

## Quick Install

### Option 1: Manual Copy

1. Copy the `klipper_pwa_plugin` folder contents to your Klipper extras directory:
   ```
   C:\Klipper\klippy\extras\klipper_pwa_plugin\
   ```

2. Edit your `printer.cfg` (already done for you):
   - Changed `save_config: False` to `save_config: True` in the `[auto_pressure_advance]` section

3. Restart Klipper

### Option 2: Using PowerShell Script

1. Run the install script:
   ```powershell
   .\install.ps1
   ```

2. The script will copy files to `C:\Klipper\klippy\extras\klipper_pwa_plugin\`

3. Edit your `printer.cfg` (already done):
   - Changed `save_config: False` to `save_config: True`

4. Restart Klipper

## Verify Installation

After restarting Klipper, run:

```gcode
PA_STATUS
```

You should see output like:
```
=== Pressure Advance Status ===
Current PA: 0.005939
Nozzle Temp: XX.XC
Target Temp: XXX.XC
Available Profiles:
  petg: 0.0245
  pla: 0.0213
  tpu: 0.009461
===============================
```

## Usage

### Full Calibration (Recommended)
```gcode
G28
PA_CALIBRATE SAVE=1
```

### Calibrate with Custom Profile
```gcode
G28
PA_CALIBRATE SAVE=1 PROFILE=pla
```

### Check Current Status
```gcode
PA_STATUS
```

### Quick Test
```gcode
PA_TEST
```

## Notes

- Your printer.cfg was already configured with `auto_pressure_advance` using a CS1237 load cell
- The plugin integrates seamlessly with your existing setup
- Calibration results are automatically saved to `printer.cfg` when you use `SAVE=1`
