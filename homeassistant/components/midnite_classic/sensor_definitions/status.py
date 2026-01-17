"""Status sensor definitions for midnite_classic integration."""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

STATUS_SENSORS = [
    # Status sensors
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
    SensorDefinition(
        key="internal_state",
        name="Internal State",
        register_group="status",
        register_address=4120,
        formula="""
            internal_state_value = value & 0xFF
            internal_state = INTERNAL_STATES.get(internal_state_value, f"Unknown ({internal_state_value})")
            value = internal_state
        """,
        entity_category="diagnostic",
    ),
]
