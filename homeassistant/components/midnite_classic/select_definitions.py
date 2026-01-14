"""Select entity definitions for midnite_classic integration."""

from __future__ import annotations

from .entity_definitions import SelectDefinition

SELECT_DEFINITIONS = [
    # Charge mode selection
    SelectDefinition(
        key="charge_mode",
        name="Charge Mode",
        register_group="settings",
        register_address=4162,
        formula="""
            from .const import CHARGE_MODES
            return CHARGE_MODES.get(value, f"Unknown ({value})")
        """,
        write_formula="""
            from .const import CHARGE_MODES
            for mode_value, mode_name in CHARGE_MODES.items():
                if mode_name == value:
                    return mode_value
            return 0  # Default to standard charging
        """,
        options=[
            "Standard",
            "PV Only",
            "Battery Only",
            "Manual",
        ],
    ),
    # Device type selection (for multi-device setups)
    SelectDefinition(
        key="device_type_override",
        name="Device Type Override",
        register_group="settings",
        register_address=4101,
        formula="""
            from .const import DEVICE_TYPES
            return DEVICE_TYPES.get(value & 0xFF, f"Unknown ({value & 0xFF})")
        """,
        write_formula="""
            from .const import DEVICE_TYPES
            for device_value, device_name in DEVICE_TYPES.items():
                if device_name == value:
                    return device_value
            return 1  # Default to Classic CC
        """,
        options=[
            "Classic CC",
            "Classic LS",
            "Classic HV",
            "Classic LV",
        ],
    ),
    # Communication mode selection
    SelectDefinition(
        key="communication_mode",
        name="Communication Mode",
        register_group="settings",
        register_address=4163,
        formula="""
            from .const import COMMUNICATION_MODES
            return COMMUNICATION_MODES.get(value, f"Unknown ({value})")
        """,
        write_formula="""
            from .const import COMMUNICATION_MODES
            for mode_value, mode_name in COMMUNICATION_MODES.items():
                if mode_name == value:
                    return mode_value
            return 0  # Default to Modbus RTU
        """,
        options=[
            "Modbus RTU",
            "Modbus TCP",
            "MidNite Network",
        ],
    ),
]

# Total: 3 select entities defined
