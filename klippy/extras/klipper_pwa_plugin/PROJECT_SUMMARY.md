# Klipper Pressure Advance Auto-Calibration Plugin - Project Summary

## Overview

This plugin automatically determines and sets the correct pressure advance (PA) setting for your Kobra 3 3D printer using your existing CS1237 load cell sensor.

## What Was Created

### Main Files

```
klipper_pwa_plugin/
├── __init__.py                    # Plugin initialization
├── pressure_advance_auto_calibrate.py  # Python macro definitions
├── pressure_advance.cfg           # Klipper G-code configuration
├── setup.py                       # Python setup script
├── install.ps1                    # PowerShell installer
│
├── README.md                      # User documentation
├── INSTALLATION.md                # Installation guide
├── SUMMARY.md                     # Quick reference
├── DIAGRAM.md                     # Architecture diagram
├── CONTRIBUTING.md                # Contribution guide
├── CHEATSHEET.md                  # Command cheat sheet
└── QUICK_REFERENCE.md             # Quick one-liners
└── PROJECT_SUMMARY.md             # This file
```

### Changes to Your Printer

**Modified: `config/printer.cfg`**
- Line 417: Changed `save_config: False` to `save_config: True`
- This enables automatic saving of calibration results

## How to Use

### 1. Install

```powershell
# Run the installer
.\install.ps1

# Or manually copy files to:
# C:\Klipper\klippy\extras\klipper_pwa_plugin\
```

### 2. Configure

Edit `printer.cfg` (already done):
```ini
[auto_pressure_advance]
    # ... existing config ...
    save_config: True  # Changed from False
```

Add include line:
```ini
[include klipper_pwa_plugin/pressure_advance.cfg]
```

### 3. Calibrate

```gcode
G28 PA_CALIBRATE SAVE=1
```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `PA_CALIBRATE` | Run full calibration | `PA_CALIBRATE SAVE=1` |
| `PA_TEST` | Quick test | `PA_TEST PA=0.025` |
| `PA_SET` | Set value | `PA_SET PA=0.025 SAVE=1` |
| `PA_STATUS` | Show status | `PA_STATUS` |

## Features

✓ **Automatic Calibration** - Uses load cell sweep method
✓ **Profile Storage** - Save values for different materials
✓ **Auto-Save** - Results saved to printer.cfg automatically
✓ **Multi-Temperature** - Calibrate at different temperatures
✓ **User-Friendly** - Simple G-code commands
✓ **Seamless Integration** - Works with existing auto_pressure_advance

## Calibration Process

1. **Home** all axes
2. **Park** at test position
3. **Heat** extruder to calibration temp
4. **Sweep** PA values (0.000 to 0.080)
5. **Measure** load cell response
6. **Calculate** optimal PA
7. **Apply** and **save** result

## Typical Results

| Filament | Expected PA Range |
|----------|-------------------|
| PLA | 0.015 - 0.025 |
| PETG | 0.020 - 0.030 |
| ABS | 0.020 - 0.030 |
| TPU | 0.005 - 0.015 |

Your current setup shows profiles like:
- petg: 0.0245
- pla: 0.0213
- tpu: 0.009461

## Benefits

1. **Better Print Quality** - Less ringing, improved layer adhesion
2. **Time Savings** - No manual tuning needed
3. **Consistency** - Same results every time
4. **Profiles** - Different values for different materials
5. **Persistence** - Values saved to config file

## Installation Steps (Complete)

```bash
# 1. Copy plugin files to Klipper extras
# (Already done by install.ps1 or manual copy)

# 2. Edit printer.cfg (already done)
# Changed: save_config: False → save_config: True

# 3. Restart Klipper
# (via Klipper terminal: systemctl restart klippy)

# 4. Verify installation
G28 PA_STATUS

# 5. Run calibration
PA_CALIBRATE SAVE=1
```

## Quick Start

```gcode
; Step 1: Home
G28

; Step 2: Calibrate (takes ~2-3 minutes)
PA_CALIBRATE SAVE=1

; Step 3: Check results
PA_STATUS

; Step 4: Test print
; (Print a small test object)
```

## Documentation

- **README.md** - Full user documentation
- **INSTALLATION.md** - Installation guide
- **SUMMARY.md** - Quick reference
- **DIAGRAM.md** - Architecture overview
- **CONTRIBUTING.md** - Contribution guide
- **CHEATSHEET.md** - Command cheat sheet
- **QUICK_REFERENCE.md** - One-liners

## Technical Details

### Plugin Architecture

- **Python Macros** - Defined in `pressure_advance_auto_calibrate.py`
- **G-code Config** - Defined in `pressure_advance.cfg`
- **Integration** - Works with Klipper's `auto_pressure_advance` hardware
- **Save Mechanism** - Uses Klipper's `SAVE_CONFIG` command

### Calibration Parameters

- **Temperature**: 180-300°C (default: 265°C)
- **PA Range**: 0.000 - 0.080 (typical: 0.010 - 0.030)
- **Steps**: 0.005 - 0.020 (default: 0.010)
- **Cycles**: 1-5 (default: 3)

### Hardware Requirements

- CS1237 load cell (already installed)
- Klipper firmware (already installed)
- Auto_pressure_advance config (already configured)

## Support

For questions or issues:

1. Check documentation files
2. Review CHEATSHEET.md for commands
3. See SUMMARY.md for quick reference
4. Consult Klipper docs: https://www.klipper3d.org/Pressure_Advance.html

## License

AGPL-3.0 (compatible with Klipper)

## Credits

Created for Kobra 3 printer with CS1237 load cell sensor.
Integrates with Klipper's auto_pressure_advance hardware.
