"""Energy sensor definitions for midnite_classic integration."""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

ENERGY_SENSORS = [
    # Energy sensors
    SensorDefinition(
        key="daily_energy",
        name="Daily Energy",
        register_group="status",
        register_address=4118,
        formula="value = value / 10.0",
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        precision=1,
    ),
    SensorDefinition(
        key="lifetime_energy",
        name="Lifetime Energy",
        register_group="energy",
        register_address=4126,
        secondary_registers=[4127],
        formula="""
            high_value = data[4127]
            value = (high_value << 16) | value
            value = value / 10.0
        """,
        device_class="energy",
        state_class="total_increasing",
        unit="kWh",
        precision=1,
    ),
    SensorDefinition(
        key="lifetime_amp_hours",
        name="Lifetime Amp-Hours",
        register_group="energy",
        register_address=4128,
        secondary_registers=[4129],
        formula="""
            high_value = data[4129]
            value = (high_value << 16) | value
            value = float(value) / 10.0
        """,
        state_class="total_increasing",
        unit="Ah",
        precision=1,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="daily_amp_hours",
        name="Daily Amp-Hours",
        register_group="energy",
        register_address=4125,
        formula="float(value)",
        state_class="total_increasing",
        unit="Ah",
        precision=0,
        entity_category="diagnostic",
    ),
]
