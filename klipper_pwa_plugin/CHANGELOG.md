# Changelog

## Version 2.0.0 - ACEPRO Integration

### New Features
- **ACEPRO Tool Change Integration**: Automatically switches PA profiles on tool change
- **Per-Tool Profile Storage**: Each ACEPRO tool can have its own PA profile
- **Automatic Profile Detection**: Plugin detects ACEPRO tool changes and applies correct PA
- **Enhanced Status Reporting**: PA_STATUS shows ACEPRO tool and handle information

### Added Files
- `pressure_advance_acepro.cfg` - ACEPRO integration macros
- `pressure_advance_acepro.py` - ACEPRO Python integration
- `ACEPRO_README.md` - ACEPRO-specific documentation
- `INSTALL_INSTRUCTIONS.md` - Installation guide
- `CHANGELOG.md` - This file

### Changed Files
- `README.md` - Updated with ACEPRO integration info
- `FINAL_INTEGRATION_GUIDE.md` - Complete integration guide

### Configuration Changes
- `save_config: True` enabled in `[auto_pressure_advance]` section
- New include lines for ACEPRO integration macros

## Version 1.0.0 - Initial Release

### New Features
- **Pressure Advance Calibration**: Automatic calibration using CS1237 load cell
- **Profile Management**: Save different PA values for different materials
- **Auto-Save**: Results automatically saved to printer.cfg
- **Quick Commands**: PA_CALIBRATE, PA_TEST, PA_SET, PA_STATUS

### Files
- `pressure_advance.cfg` - Main calibration macros
- `pressure_advance_auto_calibrate.py` - Calibration logic
- `README.md` - User documentation
- `SUMMARY.md` - Quick reference
- `CHEATSHEET.md` - Command cheat sheet

### Configuration
- Works with existing `auto_pressure_advance` hardware
- Requires `save_config: True` in `[auto_pressure_advance]` section
