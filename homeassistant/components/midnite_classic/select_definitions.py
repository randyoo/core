"""Select entity definitions for midnite_classic integration."""

from __future__ import annotations

from .entity_definitions import SelectDefinition

SELECT_DEFINITIONS = [
    # Force Charge State selector - combines the three force charge buttons
    SelectDefinition(
        key="force_charge_state",
        name="Force Charge State",
        register_group="settings",
        register_address=4160,  # Low 16 bits for force flags
        formula="""
            # Read current state from registers 4160 and 4161
            combined_value = (data.get(4161, 0) << 16) | data.get(4160, 0)

            # Check which force charge bits are set
            if combined_value & (1 << 7):  # Equalize bit (bit 7)
                return "EQ"
            elif combined_value & (1 << 6):  # Bulk/Absorb bit (bit 6)
                return "Bulk/Absorb"
            elif combined_value & (1 << 5):  # Float bit (bit 5)
                return "Float"
            else:
                # Get current charge stage from register 4120
                charge_stage_value = data.get(4120, 0) >> 8 & 0xFF
                from .const import CHARGE_STAGES
                current_stage = CHARGE_STAGES.get(charge_stage_value, "Unknown")
                return current_stage
        """,
        write_formula="""
            # Clear all force charge bits first (bits 5-7 in register 4160)
            value &= ~((1 << 7) | (1 << 6) | (1 << 5))

            # Set the appropriate bit based on selection
            if option == "EQ":
                value |= 1 << 7
            elif option == "Bulk/Absorb":
                value |= 1 << 6
            elif option == "Float":
                value |= 1 << 5

            return value & 0xFFFF
        """,
        options=[
            "Float",
            "Bulk/Absorb",
            "EQ",
        ],
    ),
    # Force Actions selector - combines remaining force actions
    SelectDefinition(
        key="force_actions",
        name="Force Actions",
        register_group="settings",
        register_address=4160,  # Low 16 bits for most force flags
        formula="""
            # Read current state from registers 4160 and 4161
            combined_value = (data.get(4161, 0) << 16) | data.get(4160, 0)

            # Check which force action bits are set
            if combined_value & (1 << 23):  # Reset faults bit (bit 23)
                return "Reset Faults"
            elif combined_value & (1 << 16):  # Reset Aeq Counts bit (bit 16)
                return "Reset Auto EQ Counter"
            elif combined_value & (1 << 11):  # Sweep/Re-track bit (bit 11)
                return "Sweep/Re-track"
            elif combined_value & (1 << 8):  # Force New Day bit (bit 8)
                return "New Day"
            elif combined_value & (1 << 4):  # Reset Info Flags bit (bit 4)
                return "Reset Info Flags"
            elif combined_value & (1 << 3):  # EEPROM Init Read bit (bit 3)
                return "EEPROM Init Read"
            elif combined_value & (1 << 2):  # EEPROM Update bit (bit 2)
                return "EEPROM Update"
            else:
                return "None"
        """,
        write_formula="""
            # Clear all force action bits first
            value &= ~((1 << 23) | (1 << 16) | (1 << 11) | (1 << 8) |
                       (1 << 4) | (1 << 3) | (1 << 2))

            # Set the appropriate bit based on selection
            if option == "Reset Faults":
                value |= 1 << 23
            elif option == "Reset Auto EQ Counter":
                value |= 1 << 16
            elif option == "Sweep/Re-track":
                value |= 1 << 11
            elif option == "New Day":
                value |= 1 << 8
            elif option == "Reset Info Flags":
                value |= 1 << 4
            elif option == "EEPROM Init Read":
                value |= 1 << 3
            elif option == "EEPROM Update":
                value |= 1 << 2

            return value & 0xFFFF
        """,
        options=[
            "None",  # No force action (default)
            "Reset Faults",
            "Reset Auto EQ Counter",
            "Sweep/Re-track",
            "New Day",
            "Reset Info Flags",
            "EEPROM Init Read",
            "EEPROM Update",
        ],
    ),
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
