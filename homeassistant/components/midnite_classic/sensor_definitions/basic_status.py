"""Basic status sensor definitions for midnite_classic integration."""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

BASIC_STATUS_SENSORS = [
    # Basic status sensors
    SensorDefinition(
        key="battery_voltage",
        name="Battery Voltage",
        register_group="status",
        register_address=4115,
        formula="value = value / 10",
        device_class="voltage",
        state_class="measurement",
        unit="V",
        precision=1,
    ),
    SensorDefinition(
        key="pv_voltage",
        name="PV Voltage",
        register_group="status",
        register_address=4116,
        formula="value = value / 10",
        device_class="voltage",
        state_class="measurement",
        unit="V",
        precision=1,
    ),
    SensorDefinition(
        key="battery_current",
        name="Battery Current",
        register_group="status",
        register_address=4117,
        formula="""
            current_value = value / 10.0
            if current_value > 32767:
                current_value = current_value - 65536
            value = current_value if abs(current_value) <= 200 else None
        """,
        device_class="current",
        state_class="measurement",
        unit="A",
        precision=1,
    ),
    SensorDefinition(
        key="power_output",
        name="Power Output",
        register_group="status",
        register_address=4119,
        formula="value",
        device_class="power",
        state_class="measurement",
        unit="W",
    ),
]
