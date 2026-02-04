"""Diagnostic sensor definitions for midnite_classic integration."""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

DIAGNOSTIC_SENSORS = [
    # InfoFlags (registers 4130-4131)
    SensorDefinition(
        key="info_flags_raw",
        name="Info Flags Raw",
        register_group="temperatures",
        register_address=4130,
        secondary_registers=[4131],
        formula="""
            # Combine two 16-bit registers into one 32-bit value
            value = (data[4131] << 16) | data[4130]
        """,
        entity_category="diagnostic",
    ),
    SensorDefinition(
        key="nite_minutes_no_pwr",
        name="Nite Minutes No Power",
        register_group="temperatures",
        register_address=4135,
        formula="value",
        device_class="duration",
        state_class="measurement",
        unit="min",
        precision=0,
        entity_category="diagnostic",
    ),
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
