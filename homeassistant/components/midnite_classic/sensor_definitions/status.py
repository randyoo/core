"""Status sensor definitions for midnite_classic integration."""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

STATUS_SENSORS = [
    # Status sensors
    # Note: internal_state sensor was removed as it's now consolidated into rest_reason
    SensorDefinition(
        key="charge_stage",
        name="Charge Stage",
        register_group="status",
        register_address=4120,
        formula="""
            charge_stage_value = (value >> 8) & 0xFF
            value = CHARGE_STAGES.get(charge_stage_value, f"Unknown ({charge_stage_value})")
        """,
        device_class="enum",
    ),
]
