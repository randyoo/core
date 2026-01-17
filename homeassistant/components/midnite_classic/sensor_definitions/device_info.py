"""Device info sensor definitions for midnite_classic integration."""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

DEVICE_INFO_SENSORS = [
    # Device info sensors - These are shown in Device Info, so hide them as entities
    SensorDefinition(
        key="device_type",
        name="Device Type",
        register_group="device_info",
        register_address=4101,
        formula="""
            device_value = value & 0xFF  # Get LSB (unit type)
            value = DEVICE_TYPES.get(device_value, f"Unknown ({device_value})")
        """,
        entity_category="diagnostic",
        enabled_by_default=False,
    ),
    SensorDefinition(
        key="firmware_version",
        name="Firmware Version",
        register_group="device_info",
        register_address=4102,
        secondary_registers=[4103],
        formula="""
            # Register 4102 contains year, register 4103 has MSB=month, LSB=day
            year = value & 0xFFFF  # Get full 16-bit value for year
            month = (data[4103] >> 8) & 0xFF  # Extract high byte (MSB)
            day = data[4103] & 0xFF  # Extract low byte (LSB)
            value = f"{year:04d}-{month:02d}-{day:02d}"
        """,
        entity_category="diagnostic",
        enabled_by_default=False,
    ),
    SensorDefinition(
        key="pcb_version",
        name="PCB Version",
        register_group="device_info",
        register_address=4101,
        formula="""
            # Extract PCB revision from UNIT_ID register (bits 8-15)
            value = (value >> 8) & 0xFF
        """,
        entity_category="diagnostic",
        enabled_by_default=False,
    ),
]
