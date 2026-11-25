# Plugin Structure & Integration

## File Structure

```
klipper_pwa_plugin/
├── __init__.py                    # Plugin initialization (empty, optional)
├── pressure_advance_auto_calibrate.py  # Python macros for Klipper
├── pressure_advance.cfg           # G-code configuration for Klipper
├── setup.py                       # Python setup script
├── install.ps1                    # PowerShell install script
├── README.md                      # User documentation
├── INSTALLATION.md                # Installation guide
├── SUMMARY.md                     # Quick reference
└── DIAGRAM.md                     # This file
```

## How It Integrates with Your Printer

```
┌─────────────────────────────────────────────────────────────────┐
│                    Your Klipper Installation                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [printer.cfg] ←─ [include klipper_pwa_plugin/pressure_advance.cfg]
│    │                                                          │
│    │                                                          │
│    ▼                                                          │
│  ┌─────────────────────────────────────────┐                 │
│  │  [auto_pressure_advance]                │                 │
│  │  sensor: cs1237                         │                 │
│  │  extruder: extruder                     │                 │
│  │  save_config: True ←─── CHANGED         │                 │
│  └─────────────────────────────────────────┘                 │
│    │                                                          │
│    ▼                                                          │
│  ┌─────────────────────────────────────────┐                 │
│  │  [extruder]                             │                 │
│  │  pressure_advance: ←─── Auto-calibrated │                 │
│  └─────────────────────────────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

New Macros Added:
┌─────────────────────────────────────────────────────────────────┐
│  PA_CALIBRATE  →  Runs AUTO_PRESSURE_ADVANCE_CALIBRATE         │
│                     Saves result to printer.cfg (if SAVE=1)     │
│                                                                 │
│  PA_TEST       →  Quick test of current PA value               │
│                                                                 │
│  PA_SET        →  Set and save specific PA value               │
│                                                                 │
│  PA_STATUS     →  Show current PA status and profiles           │
└─────────────────────────────────────────────────────────────────┘
```

## Calibration Flow

```
┌──────────────┐
│   G28        │  Home all axes
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  G1 X/Y/Z    │  Park at test position
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  M109 S265   │  Heat extruder
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────┐
│  AUTO_PRESSURE_ADVANCE_CALIBRATE   │
│  • Runs PA sweep                    │
│  • Measures load cell response      │
│  • Finds optimal PA value           │
│  • Applies to extruder              │
└──────┬──────────────────────────────┘
       │
       ▼
┌──────────────┐
│  SAVE_CONFIG │  Save to printer.cfg
└──────────────┘
```

## Data Flow

```
Load Cell (CS1237)
       │
       │ Raw pressure readings
       ▼
auto_pressure_advance (hardware)
       │
       │ Calibrated PA values
       ▼
[auto_pressure_advance.profiles]
       │
       │ Applied to extruder
       ▼
[extruder.pressure_advance]
       │
       │ Used during printing
       ▼
Better print quality (less ringing, better layer adhesion)
```

## Configuration Options

### printer.cfg Changes
```ini
[auto_pressure_advance]
    # ... existing config ...
    save_config: True  # ← Changed from False to True
```

### Plugin Files Added
```
klipper_pwa_plugin/
├── pressure_advance.cfg    # New macros
├── pressure_advance.py     # Python support
└── [docs]/                 # Documentation
```

## Usage Examples

```gcode
; 1. Home and calibrate
G28
PA_CALIBRATE SAVE=1

; 2. Calibrate with specific profile
PA_CALIBRATE SAVE=1 PROFILE=pla TEMP=220

; 3. Check status
PA_STATUS

; 4. Quick test
PA_TEST PA=0.025
```

## Integration Points

| Component | Integration |
|-----------|-------------|
| `auto_pressure_advance` | Uses existing hardware and calibration logic |
| `extruder` | Applies calibrated PA value |
| `SAVE_CONFIG` | Saves results to printer.cfg |
| `action_respond_info` | Provides feedback in Mainsail/Fluidd |

## Benefits

1. **Automatic** - No manual testing needed
2. **Profiles** - Save different values for different materials
3. **Persistent** - Results saved to printer.cfg
4. **Reusable** - Works with any load cell sensor
5. **Safe** - Uses existing auto_pressure_advance logic
