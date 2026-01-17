"""Diagnostic sensor definitions for midnite_classic integration."""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

DIAGNOSTIC_SENSORS = [
    # Diagnostic sensors
    SensorDefinition(
        key="rest_reason",
        name="Rest Reason",
        register_group="diagnostics",
        register_address=4275,
        formula="""
            value = REST_REASONS.get(value, f"Unknown ({value})")
        """,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="restart_time",
        name="Restart Time",
        register_group="status",
        register_address=4114,
        formula="value",
        device_class="duration",
        state_class="measurement",
        unit="ms",
        precision=0,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="match_point_shadow",
        name="Match Point Shadow",
        register_group="status",
        register_address=4124,
        formula="value",
        entity_category="diagnostic",
    ),
]
