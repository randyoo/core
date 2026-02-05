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
        hidden=True,
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
    # Consolidated Rest Reason sensor that shows rest reason when internal state is "Resting"
    SensorDefinition(
        key="rest_reason",
        name="Internal State/Rest Reason",
        register_group="diagnostics",
        register_address=4275,
        secondary_registers=[4120],
        formula="""
            # Get the rest reason from register 4275
            rest_reason = REST_REASONS.get(value, f"Unknown ({value})")

            # Get the internal state from register 4120
            internal_state_value = data.get(4120, 0) & 0xFF
            internal_state = INTERNAL_STATES.get(internal_state_value, f"Unknown ({internal_state_value})")

            # If internal state is "Resting", show the rest reason
            # Otherwise, show the internal state
            if internal_state == "Resting":
                value = rest_reason
            else:
                value = internal_state
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
        name="Match Point Shadow (wind)",
        register_group="status",
        register_address=4124,
        formula="value",
        entity_category="diagnostic",
        enabled_by_default=False,
    ),
]
