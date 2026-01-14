"""Button entity definitions for midnite_classic integration."""

from __future__ import annotations

from .entity_definitions import ButtonDefinition

BUTTON_DEFINITIONS = [
    ButtonDefinition(
        key="force_eeprom_update",
        name="Force EEPROM Update",
        register_group="settings",
        register_address=4160,
        write_formula="""
            from .const import FORCE_FLAGS
            flag_value = 1 << FORCE_FLAGS["ForceEEpromUpdate"]
            return flag_value
        """,
        entity_category="diagnostic",
    ),
    ButtonDefinition(
        key="reset_faults",
        name="Reset Faults",
        register_group="settings",
        register_address=4160,
        write_formula="""
            from .const import FORCE_FLAGS
            flag_value = 1 << FORCE_FLAGS["ForceResetFaults"]
            return flag_value
        """,
        entity_category="diagnostic",
    ),
    ButtonDefinition(
        key="reset_flags",
        name="Reset Flags",
        register_group="settings",
        register_address=4160,
        write_formula="""
            from .const import FORCE_FLAGS
            flag_value = 1 << FORCE_FLAGS["ResetFlags"]
            return flag_value
        """,
        entity_category="diagnostic",
    ),
]

# Total: 3 buttons defined
