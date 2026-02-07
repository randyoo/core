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
    # Note: This selector uses two registers:
    # - Register 4160 for bits 2-8, 11 (low 16 bits)
    # - Register 4161 for bits 16, 23 (high 16 bits)
    SelectDefinition(
        key="force_actions",
        name="Force Actions",
        register_group="settings",
        register_address=4160,  # Low 16 bits for most force flags
        secondary_registers=[4161],  # High 16 bits for bits 16 and 23
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
            # For bits in low register (4160): bits 2, 3, 4, 8, 11
            # For bits in high register (4161): bits 16, 23

            # Clear low bits first (bits 2, 3, 4, 8, 11 in register 4160)
            low_value = value & 0xFFFF
            low_value &= ~((1 << 11) | (1 << 8) | (1 << 4) | (1 << 3) | (1 << 2))

            # Clear high bits first (bits 16, 23 in register 4161)
            high_value = (value >> 16) & 0xFFFF
            high_value &= ~((1 << 23 >> 16) | (1 << 16 >> 16))  # bits 0 and 7 in high register

            # Set the appropriate bit based on selection
            if option == "Reset Faults":
                # Bit 23 is in high register (4161), bit position 7
                high_value |= 1 << (23 - 16)
            elif option == "Reset Auto EQ Counter":
                # Bit 16 is in high register (4161), bit position 0
                high_value |= 1 << (16 - 16)
            elif option == "Sweep/Re-track":
                # Bit 11 is in low register (4160)
                low_value |= 1 << 11
            elif option == "New Day":
                # Bit 8 is in low register (4160)
                low_value |= 1 << 8
            elif option == "Reset Info Flags":
                # Bit 4 is in low register (4160)
                low_value |= 1 << 4
            elif option == "EEPROM Init Read":
                # Bit 3 is in low register (4160)
                low_value |= 1 << 3
            elif option == "EEPROM Update":
                # Bit 2 is in low register (4160)
                low_value |= 1 << 2

            # Combine low and high values back together
            value = (high_value << 16) | low_value

            return value & 0xFFFFFFFF
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
    # Disable charge mode, device type override, and communication mode selectors for now.
    # These will be re-enabled and tested later when functionality is verified.
]

# Total: 3 select entities defined (2 active, 1 disabled)
