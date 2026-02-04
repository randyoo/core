"""Temperature sensor definitions for midnite_classic integration."""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

TEMPERATURE_SENSORS = [
    # Temperature sensors
    SensorDefinition(
        key="battery_temperature",
        name="Battery Temperature",
        register_group="temperatures",
        register_address=4132,
        formula="""
            # Convert raw 16-bit signed integer to temperature in °C (register stores tenths of °C)
            temp_value = value
            if temp_value > 32767:
                temp_value = temp_value - 65536
            value = temp_value / 10.0

            # Don't validate range - let the device's built-in logging handle it
        """,
        device_class="temperature",
        state_class="measurement",
        unit="°C",
        precision=1,
    ),
    SensorDefinition(
        key="fet_temperature",
        name="FET Temperature",
        register_group="temperatures",
        register_address=4133,
        formula="""
            # Convert raw 16-bit signed integer to temperature in °C (register stores tenths of °C)
            temp_value = value
            if temp_value > 32767:
                temp_value = temp_value - 65536
            value = temp_value / 10.0

            # Validate temperature range (-25°C to 80°C)
            if value < -25 or value > 80:
                raise ValueError("Temperature out of range")
        """,
        device_class="temperature",
        state_class="measurement",
        unit="°C",
        precision=1,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="pcb_temperature",
        name="PCB Temperature",
        register_group="temperatures",
        register_address=4134,
        formula="""
            # Convert raw 16-bit signed integer to temperature in °C (register stores tenths of °C)
            temp_value = value
            if temp_value > 32767:
                temp_value = temp_value - 65536
            value = temp_value / 10.0

            # Validate temperature range (-25°C to 80°C)
            if value < -25 or value > 80:
                raise ValueError("Temperature out of range")
        """,
        device_class="temperature",
        state_class="measurement",
        unit="°C",
        precision=1,
        entity_category="diagnostic",
    ),
]
