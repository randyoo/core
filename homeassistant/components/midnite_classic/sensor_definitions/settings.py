"""Settings sensor definitions for midnite_classic integration."""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

SETTINGS_SENSORS = [
    # Settings sensors
    SensorDefinition(
        key="logging_interval",
        name="Logging Interval",
        register_group="settings",
        register_address=4136,
        formula="value",
        device_class="duration",
        state_class="measurement",
        unit="s",
        precision=0,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="sliding_current_limit",
        name="Sliding Current Limit",
        register_group="settings",
        register_address=4152,
        formula="value = value / 10.0",
        device_class="current",
        state_class="measurement",
        unit="A",
        precision=1,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="modbus_port",
        name="Modbus Port",
        register_group="settings",
        register_address=4137,
        formula="value",
        entity_category="diagnostic",
    ),
]
