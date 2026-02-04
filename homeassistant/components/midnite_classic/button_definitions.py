"""Button entity definitions for midnite_classic integration.

Force Flag Bits (Register 4160 - Low 16 bits, Register 4161 - High 16 bits)
Combined value = ([4161] << 16) + [4160]

Each bit sets a specific force flag when written to 1.

For register 4160 (low 16 bits): Write values 0x0000-0xFFFF
For register 4161 (high 16 bits): Write the high portion directly
    e.g., bit 23 = 0x800000, write 0x80 to reg 4161 (high byte of high word)
"""

from __future__ import annotations

from .entity_definitions import ButtonDefinition


def create_force_flag_button(key: str, bit: int, name: str, register: int):
    """Create a button definition for a force flag.

    For bits > 15, the value goes to register 4161 (high 16 bits).
    For bits <= 15, the value goes to register 4160 (low 16 bits).
    """

    def write_formula(x):
        """Compute the value to write based on bit position."""
        value = 1 << bit
        if register == 4161:
            # High 16 bits (register 4161) - shift down to fit in 16-bit register
            # e.g., bit 23 = 0x800000, we write 0x80 to reg 4161
            return (value >> 16) & 0xFFFF

        # Low 16 bits (register 4160) - value fits directly
        return value & 0xFFFF

    return ButtonDefinition(
        key=f"force_{key}",
        name=name,
        register_group="settings",
        register_address=register,
        write_formula=write_formula,
        entity_category="diagnostic",
    )


# Low 16 bits (register 4160) - non-reserved bits
LOW_16_BUTTONS = [
    create_force_flag_button("eeprom_update", 2, "Force EEPROM Update", 4160),
    create_force_flag_button("eeprom_init_read", 3, "Force EEPROM Init Read", 4160),
    create_force_flag_button("reset_info_flags", 4, "Force Reset Info Flags", 4160),
    create_force_flag_button("float_charge", 5, "Force Float Charge", 4160),
    create_force_flag_button("bulk_charge", 6, "Force Bulk/Absorb Charge", 4160),
    create_force_flag_button("equalize_charge", 7, "Force Equalize Charge", 4160),
    create_force_flag_button("force_nite", 8, "Force New Day", 4160),
    create_force_flag_button("sweep_track", 11, "Force Sweep/Re-track", 4160),
]

# High 16 bits (register 4161) - non-reserved bits
HIGH_16_BUTTONS = [
    create_force_flag_button("reset_aeq_counts", 16, "Reset Aeq Counts", 4161),
    create_force_flag_button("reset_faults", 23, "Force Reset Faults", 4161),
]

BUTTON_DEFINITIONS = LOW_16_BUTTONS + HIGH_16_BUTTONS

# Total: 10 buttons defined
