"""Network sensor definitions for midnite_classic integration."""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

NETWORK_SENSORS = [
    # Network sensors - ENABLED: MAC address reading
    SensorDefinition(
        key="mac_address",
        name="MAC Address",
        register_group="device_info",
        register_address=4106,
        secondary_registers=[4107, 4108],
        formula="""
            part2 = data[4107]
            part3 = data[4108]
            mac_bytes = [
                (part3 >> 8) & 0xFF,
                part3 & 0xFF,
                (part2 >> 8) & 0xFF,
                part2 & 0xFF,
                (value >> 8) & 0xFF,
                value & 0xFF,
            ]
            value = ":".join(f"{byte:02X}" for byte in mac_bytes)
        """,
        entity_category="diagnostic",
    ),
]
