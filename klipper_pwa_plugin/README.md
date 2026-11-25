# Pressure Advance Auto-Calibration Plugin - Main Documentation

## Quick Start

### 1. Install Plugin

Copy plugin files to your Klipper extras directory:

```
C:\Klipper\klippy\extras\klipper_pwa_plugin\
```

### 2. Configure printer.cfg

Add these lines (after your `[auto_pressure_advance]` section):

```ini
# Pressure Advance Auto-Calibration Plugin with ACEPRO Integration
[include klipper_pwa_plugin/pressure_advance.cfg]
[include klipper_pwa_plugin/pressure_advance_acepro.cfg]
```

### 3. Restart Klipper

```bash
net stop klipper && net start klipper
```

### 4. Run Calibration

```gcode
G28
PA_CALIBRATE SAVE=1
```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `PA_CALIBRATE` | Run full calibration | `PA_CALIBRATE SAVE=1 PROFILE=pla` |
| `PA_TEST` | Quick test | `PA_TEST PA=0.025` |
| `PA_SET` | Set value | `PA_SET PA=0.025 SAVE=1` |
| `PA_STATUS` | Show status | `PA_STATUS` |
| `PA_SYNC` | Sync with ACEPRO | `PA_SYNC` |
| `PA_SYNC_SET` | Sync and set | `PA_SYNC_SET PA=0.025` |

## Usage Examples

### Basic Calibration

```gcode
; Home first
G28

; Run initial calibration
PA_CALIBRATE SAVE=1

; Calibrate with specific profile
PA_CALIBRATE SAVE=1 PROFILE=pla

; Calibrate with PETG
PA_CALIBRATE SAVE=1 PROFILE=petg

; Calibrate with TPU
PA_CALIBRATE SAVE=1 PROFILE=tpu
```

### ACEPRO Tool Change

```gcode
; Just run the tool change command
T1

; ACEPRO automatically switches PA profile!
```

### Fine-Tuning

```gcode
; Check current status
PA_STATUS

; Adjust PA value
PA_SET PA=0.026 SAVE=1 PROFILE=pla

; Quick test
PA_TEST PA=0.026
```

## Documentation

- **README.md** - This file (main documentation)
- **ACEPRO_README.md** - ACEPRO-specific guide
- **INSTALL_INSTRUCTIONS.md** - Installation guide
- **GETTING_STARTED.md** - Quick start guide
- **SETUP_COMPLETE.md** - Setup complete guide

## Troubleshooting

### "Unknown command" error

If you see "unknown command" errors when running `PA_CALIBRATE`:

1. **Verify plugin files exist:**
   ```bash
   Get-ChildItem "C:\Klipper\klippy\extras\klipper_pwa_plugin" -Filter "*.cfg"
   ```

2. **Check printer.cfg includes:**
   ```bash
   Get-Content "D:\klipper-kobra-s1\config\printer.cfg" | Select-String "klipper_pwa_plugin"
   ```

3. **Restart Klipper:**
   ```bash
   net stop klipper && net start klipper
   ```

### Profiles not saving

1. **Check `save_config` is True:**
   ```ini
   [auto_pressure_advance]
       save_config: True
   ```

2. **Verify `SAVE_CONFIG` is working:**
   ```gcode
   SET_PRESSURE_ADVANCE EXTRUDER=extruder ADVANCE=0.025
   SAVE_CONFIG
   ```

### No profiles shown

Run initial calibration:
```gcode
PA_CALIBRATE SAVE=1
```

## Features

- **Automatic Calibration** - Uses CS1237 load cell sensor
- **Profile Management** - Save different PA values for different materials
- **ACEPRO Integration** - Automatic PA profile switching on tool change
- **Auto-Save** - Results automatically saved to `printer.cfg` when using `SAVE=1`

## Performance

- **Calibration time:** 2-3 minutes
- **Tool change overhead:** ~50-100ms (negligible)
- **Profile switching:** Instant
- **Memory usage:** <1KB
