"""Time settings sensor definitions for midnite_classic integration.

The time-related registers in the Midnite Classic controller provide values in seconds.
This module converts these to minutes for display in Home Assistant by dividing by 60.

Register map (from Midnite Classic documentation):
- 4138: Float Time Today (seconds) → displayed in minutes
- 4139: Absorb Time Remaining - countdown timer for remaining absorb time (seconds) → displayed in minutes
- 4140-4142: Reserved
- 4143: Equalize Time Remaining (seconds) → displayed in minutes
- 4154: Absorb Time Setting - EEPROM setting for absorb duration (minutes)
"""

from __future__ import annotations

from ..entity_definitions import SensorDefinition

TIME_SETTINGS_SENSORS = [
    # Time sensors
    SensorDefinition(
        key="float_time_today",
        name="Float Time Today",
        register_group="time_settings",
        register_address=4138,
        # Convert seconds to minutes (registers provide time in seconds)
        formula="value = value / 60.0",
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
        # Convert seconds to minutes (registers provide time in seconds)
        formula="value = value / 60.0",
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
        # Convert seconds to minutes (registers provide time in seconds)
        formula="value = value / 60.0",
        device_class="duration",
        state_class="measurement",
        unit="min",
        precision=0,
        entity_category="diagnostic",
    ),
]
