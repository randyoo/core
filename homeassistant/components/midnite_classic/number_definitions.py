"""Number entity definitions for midnite_classic integration.

Formulas in number entities use expression syntax (not assignment) because
number.py evaluates formulas using eval() which doesn't support assignment statements.
For example: "float(value) / 10.0" rather than "value = value / 10.0"
"""

from __future__ import annotations

from .entity_definitions import NumberDefinition

NUMBER_DEFINITIONS = [
    # Battery voltage settings - using correct register addresses from midnite-registers.json.txt
    NumberDefinition(
        key="absorb_voltage",
        name="Absorb Voltage",
        register_group="settings",
        register_address=4149,
        # Convert raw register value to voltage (divided by 10)
        formula="float(value) / 10.0",
        write_formula="int(value * 10)",
        min_value=40.0,
        max_value=65.0,
        step=0.1,
        device_class="voltage",
        unit="V",
        precision=1,
    ),
    NumberDefinition(
        key="float_voltage",
        name="Float Voltage",
        register_group="settings",
        register_address=4150,
        # Convert raw register value to voltage (divided by 10)
        formula="float(value) / 10.0",
        write_formula="int(value * 10)",
        min_value=40.0,
        max_value=65.0,
        step=0.1,
        device_class="voltage",
        unit="V",
        precision=1,
    ),
    NumberDefinition(
        key="equalize_voltage",
        name="Equalize Voltage",
        register_group="settings",
        register_address=4151,
        # Convert raw register value to voltage (divided by 10)
        formula="float(value) / 10.0",
        write_formula="int(value * 10)",
        min_value=40.0,
        max_value=65.0,
        step=0.1,
        device_class="voltage",
        unit="V",
        precision=1,
    ),
    # Battery current limit - single setting for both absorb and float modes
    # Register 4148 = Battery output Current Limit (divided by 10, range 1-200A)
    NumberDefinition(
        key="battery_current_limit",
        name="Battery Current Limit",
        register_group="settings",
        register_address=4148,
        # Convert raw register value to current (divided by 10)
        formula="float(value) / 10.0",
        write_formula="int(value * 10)",
        min_value=1.0,
        max_value=200.0,
        step=1.0,
        device_class="current",
        unit="A",
        precision=0,
    ),
    # EEPROM Absorb Time setting - Register 4154
    NumberDefinition(
        key="absorb_time",
        name="Absorb Time",
        register_group="time_settings",
        register_address=4154,
        # Convert minutes to seconds (registers provide time in seconds, but user inputs in minutes)
        formula="float(value) / 60.0",
        write_formula="int(value * 60)",
        min_value=1.0,
        max_value=360.0,  # 6 hours in minutes
        step=1.0,
        device_class="duration",
        unit="minutes",
    ),
    NumberDefinition(
        key="equalize_time",
        name="Equalize Time",
        register_group="time_settings",
        register_address=4162,
        # Convert seconds to minutes (registers provide time in seconds)
        formula="float(value) / 60.0",
        write_formula="int(value * 60)",
        min_value=1.0,
        max_value=360.0,  # 6 hours in minutes
        step=1.0,
        device_class="duration",
        unit="minutes",
    ),
    NumberDefinition(
        key="equalize_days",
        name="Equalize Days",
        register_group="time_settings",
        register_address=4145,
        formula="value",
        write_formula="int(value)",
        min_value=0,
        max_value=365,
        step=1,
    ),
    # Temperature settings
    NumberDefinition(
        key="temp_compensation",
        name="Temperature Compensation",
        register_group="settings",
        register_address=4155,
        # Convert raw register value (percentage divided by 10)
        formula="float(value) / 10.0",
        write_formula="int(value * 10)",
        min_value=-20.0,
        max_value=20.0,
        step=1.0,
        device_class="temperature",
        unit="%/°C",
    ),
    # Network settings - DISABLED: Using unsupported 5-digit register addresses
    # NumberDefinition(
    #     key="modbus_timeout",
    #     name="Modbus Timeout",
    #     register_group="network",
    #     register_address=20496,
    #     formula="value / 10.0",
    #     write_formula="int(value * 10)",
    #     min_value=0.5,
    #     max_value=30.0,
    #     step=0.5,
    #     device_class="duration",
    #     unit="seconds",
    # ),
]

# Total: 8 number entities defined
