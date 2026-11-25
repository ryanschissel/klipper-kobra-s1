# Installation script for Klipper Pressure Advance Auto-Calibration Plugin
# Run this in PowerShell to install the plugin

$klipper_extras = "C:\Klipper\klippy\extras"

# Create the plugin directory if it doesn't exist
$plugin_dir = Join-Path $klipper_extras "klipper_pwa_plugin"
New-Item -ItemType Directory -Force -Path $plugin_dir | Out-Null

# Copy files to Klipper extras
Copy-Item -Path ".*" -Destination $plugin_dir -Recurse -Force

Write-Host "Plugin installed to: $plugin_dir"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Restart Klipper service"
Write-Host "2. Add to printer.cfg: [include $plugin_dir/pressure_advance.cfg]"
Write-Host "3. Run: G28 then PA_CALIBRATE SAVE=1"
