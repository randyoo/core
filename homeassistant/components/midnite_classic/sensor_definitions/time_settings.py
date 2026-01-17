"""Time settings sensor definitions for midnite_classic integration."""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

TIME_SETTINGS_SENSORS = [
    # Time sensors
    SensorDefinition(
        key="float_time_today",
        name="Float Time Today",
        register_group="time_settings",
        register_address=4138,
        formula="value / 60.0",
        device_class="duration",
        state_class="measurement",
        unit="min",
        precision=0,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="absorb_time_remaining",
        name="Absorb Time Remaining",
        register_group="time_settings",
        register_address=4139,
        formula="value / 60.0",
        device_class="duration",
        state_class="measurement",
        unit="min",
        precision=0,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="equalize_time_remaining",
        name="Equalize Time Remaining",
        register_group="time_settings",
        register_address=4143,
        formula="value / 60.0",
        device_class="duration",
        state_class="measurement",
        unit="min",
        precision=0,
        entity_category="diagnostic",
    ),
]
