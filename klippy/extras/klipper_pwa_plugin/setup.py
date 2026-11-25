"""
Klipper Pressure Advance Auto-Calibration Plugin
Setup script for installing the plugin in Klipper.
"""

import os
import shutil

def install_plugin(klipper_root=None):
    """
    Install the plugin to Klipper's extras directory.
    
    Args:
        klipper_root: Path to Klipper root directory. Defaults to 'C:\\Klipper'
    """
    # Default Klipper root
    if klipper_root is None:
        klipper_root = r"C:\Klipper"
    
    extras_dir = os.path.join(klipper_root, "klippy", "extras")
    plugin_name = "klipper_pwa_plugin"
    
    # Create plugin directory
    plugin_dir = os.path.join(extras_dir, plugin_name)
    
    if not os.path.exists(plugin_dir):
        os.makedirs(plugin_dir)
        print(f"Created plugin directory: {plugin_dir}")
    
    # Copy plugin files
    plugin_files = [
        "__init__.py",
        "pressure_advance_auto_calibrate.py",
        "pressure_advance.cfg",
        "README.md",
        "INSTALLATION.md",
        "SUMMARY.md",
        "install.ps1",
    ]
    
    for filename in plugin_files:
        src = os.path.join(os.path.dirname(__file__), filename)
        dst = os.path.join(plugin_dir, filename)
        
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied: {filename}")
    
    print(f"\nPlugin installed to: {plugin_dir}")
    print("\nNext steps:")
    print("1. Add to printer.cfg: [include {plugin_dir}/pressure_advance.cfg]")
    print("2. Restart Klipper")
    print("3. Run: G28 then PA_CALIBRATE SAVE=1")
    
    return plugin_dir

if __name__ == "__main__":
    install_plugin()
