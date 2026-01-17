"""Current and voltage sensor definitions for midnite_classic integration."""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

CURRENT_VOLTAGE_SENSORS = [
    # Current sensors
    SensorDefinition(
        key="pv_input_current",
        name="PV Input Current",
        register_group="status",
        register_address=4121,
        formula="""
            current_value = value / 10.0
            if current_value > 32767:
                current_value = current_value - 65536
            value = current_value if abs(current_value) <= 100 else None
        """,
        device_class="current",
        state_class="measurement",
        unit="A",
        precision=1,
        entity_category="diagnostic",
    ),
    # Voltage sensors
    SensorDefinition(
        key="voc_measured",
        name="Last Measured VOC",
        register_group="status",
        register_address=4122,
        formula="value = value / 10.0",
        device_class="voltage",
        state_class="measurement",
        unit="V",
        precision=1,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="highest_input_voltage",
        name="Highest Input Voltage",
        register_group="status",
        register_address=4123,
        formula="value = value / 10.0",
        device_class="voltage",
        state_class="measurement",
        unit="V",
        precision=1,
        entity_category="diagnostic",
    ),
]
