"""Helper for processing temperature readings from Midnite Classic devices."""

from __future__ import annotations

import logging
from typing import TypedDict

_LOGGER = logging.getLogger(__name__)

TEMPERATURE_LIMITS: dict[str, tuple[float, float]] = {
    "temp_ambient": (-50.0, 125.0),
    "temp_pcb": (-40.0, 100.0),
    # Note: battery_temperature now uses formula instead of helper
}

TEMPERATURE_SENSOR_KEYS = ["temp_ambient", "temp_pcb"]


class TemperatureContext(TypedDict):
    """Context for temperature tracking."""

    last_value: float | None
    last_update_time: float | None


class TemperatureHelper:
    """Helper class for processing and validating temperature readings."""

    def __init__(self) -> None:
        """Initialize the temperature helper."""
        self._context: dict[str, TemperatureContext] = {
            key: {"last_value": None, "last_update_time": None}
            for key in TEMPERATURE_SENSOR_KEYS
        }

    def process_temperature(
        self,
        sensor_key: str,
        raw_value: float | None,
        register_address: int,
    ) -> float | None:
        """Process a temperature reading from a Midnite Classic device.

        Args:
            sensor_key: The key identifying the sensor type
            raw_value: The raw value from the register (can be None)
            register_address: The register address for debugging

        Returns:
            Processed temperature in °C, or None if invalid
        """
        if raw_value is None:
            return None

        try:
            temp_c = self._raw_to_temperature(raw_value)

            # Validate temperature range
            min_temp, max_temp = TEMPERATURE_LIMITS.get(
                sensor_key,
                (-100.0, 200.0),  # Default fallback limits
            )
            if not (min_temp <= temp_c <= max_temp):
                _LOGGER.warning(
                    "Temperature out of range for %s at register %s: %.1f°C (expected %.1f-%.1f°C)",
                    sensor_key,
                    register_address,
                    temp_c,
                    min_temp,
                    max_temp,
                )
                return None

        except (ValueError, TypeError):
            _LOGGER.error(
                "Invalid temperature value for %s at register %s: %s",
                sensor_key,
                register_address,
                raw_value,
            )
            return None
        else:
            # Check for fluctuations
            result = self._check_fluctuations(sensor_key, temp_c)
            if result is not None:
                return result
            return None

    def _raw_to_temperature(self, raw_value: float) -> float:
        """Convert raw 16-bit signed integer to temperature in °C.

        Midnite Classic devices store temperatures as 16-bit signed integers
        representing tenths of a degree Celsius.
        """
        # Check if value is negative (signed 16-bit integer)
        if raw_value > 32767:
            temp_c = raw_value - 65536
        else:
            temp_c = raw_value

        return temp_c / 10.0

    def _check_limits(self, sensor_key: str, temp_c: float) -> float | None:
        """Validate that temperature is within reasonable limits for the sensor type.

        Args:
            sensor_key: The key identifying the sensor type
            temp_c: Temperature in °C

        Returns:
            Validated temperature or last known good value if out of range
        """
        min_temp, max_temp = TEMPERATURE_LIMITS.get(
            sensor_key,
            (-100.0, 200.0),  # Default fallback limits
        )
        if not (min_temp <= temp_c <= max_temp):
            _LOGGER.warning(
                "Temperature out of range for %s: %.1f°C (expected %.1f-%.1f°C)",
                sensor_key,
                temp_c,
                min_temp,
                max_temp,
            )
            return None
        return temp_c

    def _check_fluctuations(
        self, sensor_key: str, temp_c: float | None
    ) -> float | None:
        """Check for unreasonable temperature fluctuations between readings.

        Args:
            sensor_key: The key identifying the sensor type
            temp_c: Temperature in °C (can be None if validation failed)

        Returns:
            Validated temperature or previous value if fluctuation is too large
        """
        if temp_c is None:
            return None

        context = self._context[sensor_key]
        last_value = context["last_value"]

        if last_value is not None and abs(temp_c - last_value) > 20.0:
            _LOGGER.warning(
                "Large temperature fluctuation detected for %s: %.1f°C (previous: %.1f°C)",
                sensor_key,
                temp_c,
                last_value,
            )
            return last_value

        context["last_value"] = temp_c
        return temp_c
