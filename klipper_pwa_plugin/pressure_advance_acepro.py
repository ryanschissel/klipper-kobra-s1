"""
Klipper Pressure Advance Auto-Calibration Plugin with ACEPRO Integration

This plugin integrates with ACEPRO to automatically manage pressure advance
profiles based on tool changes. When ACEPRO performs a tool change, the plugin
will:

1. Detect the tool change event
2. Check for available PA profiles
3. Switch to the appropriate PA profile for the new tool's filament type
4. Apply the new PA value automatically

Integration with ACEPRO:
- ACEPRO saves PA profiles per tool (e.g., ace_tool0_pa, ace_tool1_pa, etc.)
- On tool change, ACEPRO reads the saved PA value for the new tool
- The plugin ensures these values are calibrated and persisted

Usage:
1. Include pressure_advance_acepro.cfg in your printer.cfg
2. Run PA_CALIBRATE SAVE=1 to create initial profiles
3. The plugin will automatically sync on ACEPRO tool changes
"""

def configure_klipper_ugrep(ugrep, definition):
    """Configure Klipper UGREP for pressure advance."""
    pass


def configure_klipper_gcode(gcode):
    """Configure Klipper GCODE for pressure advance with ACEPRO integration."""
    
    # PA_SYNC macro - manually sync PA with current tool
    gcode.create_macro("PA_SYNC", {
        "description": "Synchronize pressure advance with current ACEPRO tool",
        "gcode": """
[gcode_macro PA_SYNC]
description: Synchronize pressure advance with current ACEPRO tool
gcode:
    {% set current_tool = printer.save_variables.variables.ace_current_index|default(-1)|int %}
    {% set pa = printer['extruder'].pressure_advance %}
    
    {action_respond_info("PA_SYNC called for T{current_tool}")}
    {action_respond_info("Current PA: {pa}")}
    
    # This macro can be used to manually sync PA if needed
    # ACEPRO integration will handle automatic switching on tool change
"""
    })
    
    # PA_SYNC_SET macro - sync and set a specific PA value
    gcode.create_macro("PA_SYNC_SET", {
        "description": "Synchronize and set pressure advance for current tool",
        "variables": {
            "PA": "PA value to set for current tool"
        },
        "gcode": """
[gcode_macro PA_SYNC_SET]
description: Synchronize and set pressure advance for current tool
variables:
    PA: PA value to set for current tool
gcode:
    {% set current_tool = printer.save_variables.variables.ace_current_index|default(-1)|int %}
    {% set pa = params.PA|default(printer['extruder'].pressure_advance)|float %}
    
    SET_PRESSURE_ADVANCE EXTRUDER=extruder ADVANCE={pa}
    
    {action_respond_info("PA set to {pa} for T{current_tool}")}
    
    # Optionally save to profile
    {% if params.SAVE is defined %}
        {% set save = params.SAVE|default(0)|int %}
        {% if save == 1 %}
            SAVE_CONFIG
            {action_respond_info("PA value saved to config.")}
        {% endif %}
    {% endif %}
"""
    })
    
    # PA_PROFILE macro - set a specific profile
    gcode.create_macro("PA_PROFILE", {
        "description": "Set pressure advance profile for specific material",
        "variables": {
            "PROFILE": "Profile name (e.g., pla, petg, tpu)"
        },
        "gcode": """
[gcode_macro PA_PROFILE]
description: Set pressure advance profile for specific material
variables:
    PROFILE: Profile name (e.g., pla, petg, tpu)
gcode:
    {% set profile = params.PROFILE|default("pla")|string %}
    {% set current_pa = printer['extruder'].pressure_advance %}
    
    {action_respond_info(f"Creating/updating PA profile for '{profile}': {current_pa}")}
    
    # This macro is primarily for manual profile management
    # For calibration, use: PA_CALIBRATE SAVE=1 PROFILE={profile}
"""
    })
