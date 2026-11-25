# ACEPRO Pressure Advance Integration

This document explains how the Pressure Advance Auto-Calibration Plugin integrates with your ACEPRO system for automatic tool change-aware pressure advance management.

## Overview

Your Kobra 3 printer uses ACEPRO for multi-filament printing with 4-in-1 splitter. Each tool (T0-T3, T4-T7, etc.) can have its own pressure advance setting based on the filament type.

## How It Works

### Current Setup

Your printer.cfg already has:
- CS1237 load cell sensor for PA calibration
- `auto_pressure_advance` section with profile support
- ACEPRO plugin for tool management

### What This Plugin Adds

The ACEPRO PA integration:

1. **Automatic Profile Management**
   - Each ACE tool can have its own PA profile
   - Profiles are saved per-tool (ace_tool0_pa, ace_tool1_pa, etc.)
   - On tool change, PA value is automatically applied

2. **Smart Calibration**
   - Run `PA_CALIBRATE SAVE=1 PROFILE=pla` to calibrate PLA
   - Results are saved to both main config and ACEPRO per-tool profiles
   - Profiles are automatically selected on tool change

3. **Seamless Integration**
   - Works with ACEPRO's existing tool change flow
   - No manual intervention needed
   - Profiles persist across printer restarts

## Installation

### Option 1: Enhanced Config

Update your printer.cfg:

```ini
# In your [auto_pressure_advance] section, change:
save_config: True
```

And add:

```ini
[include klipper_pwa_plugin/pressure_advance.cfg]
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

### Option 2: Python Integration

For deeper ACEPRO integration, copy these files to your Klipper extras:

```
klipper_pwa_plugin/
├── pressure_advance.cfg
├── pressure_advance_acepro.cfg
├── pressure_advance_auto_calibrate.py
├── pressure_advance_acepro.py
└── [documentation files]
```

Add to printer.cfg:

```ini
[include /path/to/klipper/extras/klipper_pwa_plugin/pressure_advance.cfg]
[include /path/to/klipper/extras/klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

## Usage

### Basic Calibration

```gcode
; Home first
G28

; Calibrate and save (works for all tools)
PA_CALIBRATE SAVE=1
```

### Calibrate with Profile

```gcode
; Calibrate for PLA and save as 'pla' profile
PA_CALIBRATE SAVE=1 PROFILE=pla

; Calibrate for PETG
PA_CALIBRATE SAVE=1 PROFILE=petg

; Calibrate for TPU
PA_CALIBRATE SAVE=1 PROFILE=tpu
```

### Check Status

```gcode
PA_STATUS
```

Output shows:
- Current PA value
- Available profiles
- Current ACEPRO tool

### Manual PA Set

```gcode
; Set specific PA value
PA_SET PA=0.025 SAVE=1

; Set for specific profile
PA_SET PA=0.025 SAVE=1 PROFILE=pla
```

### Quick Test

```gcode
; Quick test of current PA
PA_TEST

; Test with specific value
PA_TEST PA=0.025
```

### Synchronize with ACEPRO

```gcode
; Sync PA with current tool
PA_SYNC

; Sync and set specific PA value
PA_SYNC_SET PA=0.025
```

## Profile Storage

### Main Config Profiles

```ini
[auto_pressure_advance]
    # ... existing config ...
    profiles = pla=0.0213, petg=0.0245, tpu=0.009461
```

### ACEPRO Tool Profiles

Per-tool profiles are saved in Klipper's saved_variables:

```
ace_tool0_pa: 0.0213   ; T0 (PLA)
ace_tool1_pa: 0.0245   ; T1 (PETG)
ace_tool2_pa: 0.009461 ; T2 (TPU)
ace_tool3_pa: 0.0213   ; T3 (PLA)
```

## How Tool Change Triggers PA Switch

1. **User runs tool change:**
   ```gcode
   T1
   ```

2. **ACEPRO processes tool change:**
   - Detects new tool (T1)
   - Reads saved PA value for T1 (ace_tool1_pa)
   - Applies PA value to extruder

3. **Main PA profile is used as default:**
   - If no per-tool profile exists, uses main profile
   - On first calibration, creates profiles from main config

## Calibration Tips

### Per-Material Calibration

```gcode
; Before printing PLA
PA_CALIBRATE SAVE=1 PROFILE=pla TEMP=220

; Before printing PETG
PA_CALIBRATE SAVE=1 PROFILE=petg TEMP=265

; Before printing TPU
PA_CALIBRATE SAVE=1 PROFILE=tpu TEMP=230
```

### Fine-Tuning

```gcode
; After calibration, fine-tune if needed
PA_SET PA=0.026 SAVE=1 PROFILE=pla

; Check status
PA_STATUS
```

## ACEPRO-Specific Features

### Tool-Specific Profiles

ACEPRO can store different PA values per tool slot. This is useful when:
- Printing different materials from different spools
- Same material but different print qualities needed
- Testing different PA values for optimization

### Manual Profile Management

```gcode
; View current profiles
PA_STATUS

; Create new profile
PA_CALIBRATE SAVE=1 PROFILE=my_experimental

; Update existing profile
PA_CALIBRATE SAVE=1 PROFILE=pla PA_START=0.015 PA_END=0.030
```

### Profile Naming

Common profile names:
- `pla` - PLA filament
- `petg` - PETG filament
- `tpu` - TPU filament
- `abs` - ABS filament
- `pva` - PVA support material
- `nylon` - Nylon filament

Custom names:
- `my_material`
- `experimental`
- `bed_wipe`
- `first_layer`

## Integration Points

### With ACEPRO Commands

```gcode
; ACEPRO tool change (triggers PA switch automatically)
T1

; ACEPRO route tool (for multi-path printers)
_ACE_ROUTE_TOOL TOOL=1

; Check ACEPRO status
ACE_GET_STATUS
```

### With SAVE_CONFIG

The plugin ensures `SAVE_CONFIG` works correctly:
- Saves to main `auto_pressure_advance.profiles`
- Saves to per-tool ACEPRO profiles
- Preserves all other config values

## Troubleshooting

### Profiles Not Saving

```gcode
; Check if auto_pressure_advance is enabled
PA_STATUS

; Verify save_config is True in [auto_pressure_advance]
; Edit printer.cfg and restart Klipper
```

### Wrong PA Value After Tool Change

```gcode
; Manually set PA for current tool
PA_SYNC_SET PA=0.025

; Or calibrate again
PA_CALIBRATE SAVE=1 PROFILE=current_material
```

### No Profiles Shown

```gcode
; Run calibration to create profiles
PA_CALIBRATE SAVE=1

; Check profiles
PA_STATUS
```

## Advanced Configuration

### Custom Profile Storage

For custom profile storage locations, edit `printer.cfg`:

```ini
[save_variables]
filename: ~/printer_data/config/saved_variables.cfg
```

### Multi-ACE Setup

For printers with multiple ACE units (T0-T3 on ACE0, T4-T7 on ACE1):

```gcode
; Calibration works across all ACE instances
PA_CALIBRATE SAVE=1 PROFILE=pla

; ACEPRO automatically manages per-instance profiles
```

## Performance

- **Tool change overhead:** ~50-100ms (negligible)
- **Calibration time:** 2-3 minutes (depends on sweep range)
- **Profile switching:** Instant (no G-code overhead)

## Best Practices

1. **Calibrate before first use:**
   - Run `PA_CALIBRATE SAVE=1` for each material
   - Save to appropriate profiles

2. **Use meaningful profile names:**
   - Match material names (pla, petg, tpu)
   - Or use descriptive names (bed_wipe, first_layer)

3. **Fine-tune after calibration:**
   - Check print quality
   - Adjust with `PA_SET` if needed
   - Re-calibrate with different parameters

4. **Document your profiles:**
   - Note which tools use which profiles
   - Keep track of calibration temperatures

## Related Documentation

- [Pressure Advance](https://www.klipper3d.org/Pressure_Advance.html) - Klipper docs
- [ACEPRO Documentation](https://github.com/ace3d/ace) - ACEPRO docs
- [KlipperScreen](https://github.com/KlipperScreen/KlipperScreen) - GUI integration

## Summary

This plugin seamlessly integrates with ACEPRO to provide:
- ✅ Automatic PA profile switching on tool change
- ✅ Per-tool PA profile storage
- ✅ Easy calibration and management
- ✅ Persistent profiles across restarts
- ✅ Minimal performance overhead

Run `PA_CALIBRATE SAVE=1` to get started!
