"""Text entity definitions for midnite_classic integration."""

from __future__ import annotations

from .entity_definitions import TextDefinition

TEXT_DEFINITIONS = [
    # Device name
    TextDefinition(
        key="device_name",
        name="Device Name",
        register_group="settings",
        register_address=4170,
        secondary_registers=[4171, 4172],
        formula="""
            chars = []
            for reg in [value] + data.get("secondary_registers", []):
                chars.extend([
                    chr((reg >> 8) & 0xFF),
                    chr(reg & 0xFF),
                ])
            return "".join(chars).rstrip("\x00")
        """,
        write_formula="""
            text_bytes = list(text.encode("ascii")[:24])
            text_bytes += [0] * (24 - len(text_bytes))
            registers = []
            for i in range(0, 24, 2):
                reg_value = (text_bytes[i] << 8) | text_bytes[i + 1]
                registers.append(reg_value)
            return registers
        """,
        max_length=24,
    ),
]

# Total: 1 text entity defined
