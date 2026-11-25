# Contributing to the Pressure Advance Auto-Calibration Plugin

Thank you for your interest in contributing! This document outlines how to extend and improve the plugin.

## Project Goals

- **Automate PA calibration** - Make it easy to find optimal pressure advance values
- **Profile-based storage** - Support multiple material profiles
- **Seamless integration** - Work with existing Klipper `auto_pressure_advance` hardware
- **User-friendly** - Simple G-code commands for common tasks

## Architecture

The plugin consists of:

1. **`pressure_advance.cfg`** - Klipper G-code macros (`.cfg` files)
2. **`pressure_advance_auto_calibrate.py`** - Python macro definitions
3. **Documentation** - User guides and installation instructions

## Adding New Features

### Adding a New Macro

To add a new G-code macro, append to `pressure_advance.cfg`:

```ini
[gcode_macro NEW_FEATURE]
description: Description of the feature
variables:
    PARAM1: Description
gcode:
    ; Macro logic here
```

### Adding Python Support

To add Python logic, append to `pressure_advance_auto_calibrate.py`:

```python
def configure_klipper_gcode(gcode):
    gcode.create_macro("NEW_FEATURE", {
        "description": "...",
        "variables": {...},
        "gcode": """..."""
    })
```

## Testing

### Manual Testing

1. Install the plugin in your Klipper installation
2. Run `PA_STATUS` to verify macros are loaded
3. Test `PA_CALIBRATE` and verify results
4. Check that `SAVE_CONFIG` updates `printer.cfg`

### Automated Testing

Add test cases to validate:
- Macro definitions are valid Klipper syntax
- Parameters are properly parsed
- `SAVE_CONFIG` writes correct format

## Documentation

### Adding Examples

Create `EXAMPLES.md` with usage examples:

```markdown
## Example 1: PLA Calibration
```gcode
G28
PA_CALIBRATE SAVE=1 PROFILE=pla
PA_STATUS
```
```

## Versioning

Use semantic versioning:
- **v1.0.0** - Initial release (this version)
- **v1.1.0** - Add new features
- **v1.1.1** - Bug fixes

## License

This plugin is compatible with Klipper's AGPL license.

## Support

For questions or issues:
- Check the [README.md](README.md)
- Review the [INSTALLATION.md](INSTALLATION.md)
- See [SUMMARY.md](SUMMARY.md) for quick reference
