# How the Pressure Advance Plugin Works

## Plugin Structure

The plugin consists of two types of files:

### 1. G-code Macros (.cfg files)

**Location in Klipper:**
```
C:\Klipper\klippy\extras\klipper_pwa_plugin\
├── pressure_advance.cfg
└── pressure_advance_acepro.cfg
```

**How they're loaded:** Via `[include]` statements in `printer.cfg`:
```ini
[include klipper_pwa_plugin/pressure_advance.cfg]
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

**What they do:**
- Define G-code macros like `PA_CALIBRATE`, `PA_TEST`, `PA_SET`, etc.
- These are called with G-code commands from the Mainsail/Fluidd interface
- Execute Klipper's Python API commands (like `SET_PRESSURE_ADVANCE`, `SAVE_CONFIG`, etc.)

### 2. Python Code (.py files)

**Location in Klipper:**
```
C:\Klipper\klippy\extras\klipper_pwa_plugin\
├── pressure_advance.cfg
├── pressure_advance_acepro.cfg
└── pressure_advance_acepro.py  # Python code (auto-loaded by Klipper)
```

**How they're loaded:** Klipper automatically scans the `klippy/extras/` directory and loads all `.py` files.

**What they do:**
- Can define Python functions that extend Klipper's functionality
- Can hook into Klipper's event system
- Can add custom G-code macros via the `gcode` object
- Can integrate with other Klipper objects

## Why Both Types of Files?

### .cfg Files (G-code Macros)
- **User-facing** - Called with simple G-code commands
- **Easy to use** - No need to know Python
- **Configurable** - Parameters defined in the macro itself
- **Loaded via includes** - Must be in printer.cfg

### .py Files (Python Code)
- **Backend logic** - Can do more complex operations
- **Event hooks** - Can respond to Klipper events
- **Integration** - Can interact with other Klipper objects
- **Auto-loaded** - Just needs to be in the extras directory

## Your Current Setup

### printer.cfg Configuration:
```ini
# Pressure Advance Auto-Calibration Plugin with ACEPRO Integration
[auto_pressure_advance]
save_config: True

[include klipper_pwa_plugin/pressure_advance.cfg]
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

### What This Means:
1. **`[auto_pressure_advance]`** - Hardware plugin section for load cell calibration
2. **`[include ...]`** - Loads the G-code macros from the plugin
3. **Python files (.py)** - Auto-loaded by Klipper from the extras directory

## How ACEPRO Integration Works

The ACEPRO integration happens through:

1. **G-code macros** (`.cfg` files):
   - `PA_STATUS` - Shows current PA and profiles
   - `PA_SYNC` - Synchronizes with ACEPRO tool
   - `PA_SYNC_SET` - Sets PA and syncs with ACEPRO

2. **ACEPRO state** (from ACEPRO plugin):
   - ACEPRO saves per-tool PA values in `saved_variables.cfg`
   - On tool change, ACEPRO reads the saved PA value
   - ACEPRO applies it automatically

3. **Python integration** (`.py` files):
   - Can hook into ACEPRO's Python API
   - Can respond to ACEPRO events
   - Can extend ACEPRO functionality

## File Locations Summary

| File Type | Location | How Loaded | Purpose |
|-----------|----------|------------|---------|
| `.cfg` | `klippy/extras/<plugin>/` | Via `[include]` | G-code macros |
| `.py` | `klippy/extras/<plugin>/` | Auto-loaded | Python code |
| `printer.cfg` | `config/` | Main config | Includes plugin |

## Common Questions

### Q: Do I need both .cfg and .py files?
**A:** Not necessarily. Simple macros can be in `.cfg` files. Complex logic can be in `.py` files.

### Q: Where do I put the plugin files?
**A:** Both `.cfg` and `.py` files go in `C:\Klipper\klippy\extras\klipper_pwa_plugin\`

### Q: How does Klipper know to load the .py files?
**A:** Klipper automatically scans the `klippy/extras/` directory and loads all `.py` files.

### Q: Can I use .py files without .cfg files?
**A:** Yes, but you'd need to use the Python API directly (via Moonraker or KlipperScreen).

### Q: Can I use .cfg files without .py files?
**A:** Yes, this is the simplest setup. Just use the G-code macros defined in the `.cfg` files.

## Summary

- **`.cfg` files** = G-code macros loaded via `[include]` statements
- **`.py` files** = Python code auto-loaded by Klipper
- **Both work together** to provide a complete plugin experience
- **For your use case**, the `.cfg` files are what you'll use most (via G-code commands)
- **The `.py` files** provide backend support and can be extended if needed
