"""Support for Midnite Classic sensor platform."""

from __future__ import annotations

import logging
import traceback
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory  # type: ignore[attr-defined]
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    AUX1_FUNCTIONS,
    AUX2_FUNCTIONS,
    CHARGE_STAGES,
    DEVICE_TYPES,
    DOMAIN,
    FORCE_FLAGS,
    INTERNAL_STATES,
    IP_SETTINGS_FLAGS,
    MPPT_MODES,
    REST_REASONS,
)
from .coordinator import MidniteClassicCoordinator
from .sensor_definitions import SENSOR_DEFINITIONS
from .temperature_helper import TEMPERATURE_SENSOR_KEYS, TemperatureHelper

_LOGGER = logging.getLogger(__name__)

# Global temperature helper instance for all sensors
_TEMP_HELPER = TemperatureHelper()


async def async_setup_entry(  # pylint: disable=hass-argument-type
    hass: HomeAssistant,
    entry: Any,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Midnite Classic sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []
    for definition in SENSOR_DEFINITIONS:
        # Skip network registers (5-digit addresses starting with 204)
        if not str(definition.register_address).startswith("204"):
            sensor_class = create_sensor_class(definition)
            sensors.append(sensor_class(coordinator, entry, definition))

    async_add_entities(sensors)


def _normalize_formula_indentation(formula_str: str) -> str:
    """Normalize indentation in formula strings to handle copy-pasted code."""
    lines = formula_str.split("\n")
    if not lines:
        return formula_str

    # Find the minimum indentation (leading whitespace)
    min_indent = None
    for line in lines:
        stripped = line.lstrip()
        if stripped:  # Only consider non-empty lines
            indent = len(line) - len(stripped)
            if min_indent is None or indent < min_indent:
                min_indent = indent

    # Remove the minimum indentation from all lines
    if min_indent is not None and min_indent > 0:
        normalized_lines = []
        for line in lines:
            if len(line) >= min_indent and line[:min_indent].isspace():
                normalized_lines.append(line[min_indent:])
            else:
                normalized_lines.append(line)
        formula_str = "\n".join(normalized_lines)

    # Replace 'return' statements with assignment to value variable
    # This is needed because exec() doesn't support return statements
    return formula_str.replace("return ", "value = ")


class DynamicSensor(CoordinatorEntity[MidniteClassicCoordinator], SensorEntity):
    """Dynamic sensor based on definition."""

    def __init__(  # pylint: disable=hass-return-type
        self, coordinator: MidniteClassicCoordinator, entry: Any, definition: Any
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._definition = definition

        # Set basic attributes from definition
        self._attr_name = definition.name
        self._attr_unique_id = f"{entry.entry_id}_{definition.key}"

        # Set device class if defined
        self._set_device_class()

        # Set unit of measurement if defined
        self._set_unit_of_measurement()

        # Set state class if defined
        self._set_state_class()

        # Set precision if defined
        self._set_precision()

        # Set entity category if defined
        self._set_entity_category()

        # Set enabled_by_default flag if defined
        self._set_enabled_by_default()

    def _set_device_class(self) -> None:
        """Set the device class attribute."""
        if hasattr(self._definition, "device_class") and self._definition.device_class:
            self._attr_device_class = getattr(
                SensorDeviceClass, self._definition.device_class.upper(), None
            )

    def _set_unit_of_measurement(self) -> None:
        """Set the unit of measurement attribute."""
        if hasattr(self._definition, "unit"):
            self._attr_native_unit_of_measurement = self._definition.unit

    def _set_state_class(self) -> None:
        """Set the state class attribute."""
        if hasattr(self._definition, "state_class") and self._definition.state_class:
            self._attr_state_class = getattr(
                SensorStateClass, self._definition.state_class.upper(), None
            )

    def _set_precision(self) -> None:
        """Set the suggested display precision attribute."""
        if hasattr(self._definition, "precision"):
            self._attr_suggested_display_precision = self._definition.precision

    def _set_entity_category(self) -> None:
        """Set the entity category attribute."""
        if (
            hasattr(self._definition, "entity_category")
            and self._definition.entity_category
        ):
            self._attr_entity_category = getattr(
                EntityCategory, self._definition.entity_category.upper(), None
            )

    def _set_enabled_by_default(self) -> None:
        """Set the enabled by default flag."""
        if hasattr(self._definition, "enabled_by_default"):
            self._attr_entity_registry_enabled_default = (
                self._definition.enabled_by_default
            )

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device info."""
        # Get device info from coordinator (includes MAC address from modbus)
        return self.coordinator.update_device_info()

    @property
    def native_value(  # pylint: disable=hass-return-type
        self,
    ) -> Any | None:
        """Return the state of the sensor."""
        # Check for valid coordinator data
        if not self.coordinator.data or "data" not in self.coordinator.data:
            return None

        group_data = self.coordinator.data["data"].get(self._definition.register_group)
        if not group_data:
            return None

        value = group_data.get(self._definition.register_address)
        if value is None:
            return None

        # DEBUG: Log raw register values for temperature sensors to help diagnose issues
        if self._definition.key in TEMPERATURE_SENSOR_KEYS and isinstance(
            value, (int, float)
        ):
            _LOGGER.debug(
                "Raw temperature register value for %s at register %s: %s",
                self._definition.key,
                self._definition.register_address,
                value,
            )

        # Apply formula if defined (string-based only for safety)
        if hasattr(self._definition, "formula") and self._definition.formula:
            result = self._apply_formula(value, group_data)
            if result is not None:
                return result

        # Apply temperature helper for temperature sensors without formulas
        # Note: battery_temperature now uses formula instead of helper
        if self._definition.key in TEMPERATURE_SENSOR_KEYS and isinstance(
            value, (int, float)
        ):
            processed_temp = _TEMP_HELPER.process_temperature(
                self._definition.key, value, self._definition.register_address
            )
            # Log debug info for improbable temperature values
            if processed_temp is not None:
                if processed_temp < -60.0 or processed_temp > 130.0:
                    _LOGGER.warning(
                        "Unusual temperature value detected for %s at register %s: %.1f°C (raw_register_value: %s)",
                        self._definition.key,
                        self._definition.register_address,
                        processed_temp,
                        value,
                    )
                elif abs(processed_temp) > 1000.0:
                    _LOGGER.error(
                        "EXTREME temperature value detected for %s at register %s: %.1f°C (raw_register_value: %s), suggesting a device communication error",
                        self._definition.key,
                        self._definition.register_address,
                        processed_temp,
                        value,
                    )
            return processed_temp

        return value

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # For write-protected entities, we still want to show them as available
        # but with a warning when write operations are attempted
        return super().available

    def _apply_formula(self, value: Any, group_data: dict[int, Any]) -> Any | None:
        """Apply formula to the raw value."""
        try:
            # Create a data dict for formulas that need secondary registers
            data_dict = {self._definition.register_address: value}
            for reg in getattr(self._definition, "secondary_registers", []):
                if reg in group_data:
                    data_dict[reg] = group_data[reg]

            # Normalize and strip whitespace from formula
            formula_str = _normalize_formula_indentation(
                self._definition.formula
            ).strip()

            local_vars = {
                "value": value,
                "data": data_dict,
                "CHARGE_STAGES": CHARGE_STAGES,
                "INTERNAL_STATES": INTERNAL_STATES,
                "REST_REASONS": REST_REASONS,
                "DEVICE_TYPES": DEVICE_TYPES,
                "FORCE_FLAGS": FORCE_FLAGS,
                "MPPT_MODES": MPPT_MODES,
                "IP_SETTINGS_FLAGS": IP_SETTINGS_FLAGS,
                "AUX1_FUNCTIONS": AUX1_FUNCTIONS,
                "AUX2_FUNCTIONS": AUX2_FUNCTIONS,
            }
            exec(  # noqa: S102
                compile(formula_str, "<string>", "exec"),
                {"__name__": "__main__"},
                local_vars,
            )
        except Exception as exc:  # noqa: BLE001
            # Catch all exceptions from exec() which can raise any exception type
            # including custom ones defined in user formulas. We log and return None.
            _LOGGER.error(
                "Error applying formula for %s (register %s): %s. Formula: %s",
                self._definition.key,
                self._definition.register_address,
                exc,
                formula_str,
            )
            traceback.print_exc()
            return None

        result = local_vars.get("value")

        # DEBUG LOGGING - Enhanced for enum sensors
        if self._definition.key in [
            "charge_stage",
            "internal_state",
            "rest_reason",
            "device_type",
        ]:
            _LOGGER.debug(
                "Sensor %s: raw_value=%s, formula_result=%s, CHARGE_STAGES_keys=%s, INTERNAL_STATES_keys=%s, REST_REASONS_keys=%s, DEVICE_TYPES_keys=%s",
                self._definition.key,
                value,
                result,
                list(CHARGE_STAGES.keys()),
                list(INTERNAL_STATES.keys()),
                list(REST_REASONS.keys()),
                list(DEVICE_TYPES.keys()),
            )
            if self._definition.key == "charge_stage":
                charge_stage_value = (value >> 8) & 0xFF
                _LOGGER.debug(
                    "Charge stage extraction: raw=0x%04X, extracted=%d, lookup_result=%s",
                    value,
                    charge_stage_value,
                    CHARGE_STAGES.get(charge_stage_value),
                )
            elif self._definition.key == "internal_state":
                internal_state_value = value & 0xFF
                _LOGGER.debug(
                    "Internal state extraction: raw=0x%04X, extracted=%d, lookup_result=%s",
                    value,
                    internal_state_value,
                    INTERNAL_STATES.get(internal_state_value),
                )

        # Apply temperature helper for temperature sensors
        if self._definition.key in TEMPERATURE_SENSOR_KEYS and isinstance(
            result, (int, float)
        ):
            # DEBUG: Log ALL temperature values unconditionally for debugging
            _LOGGER.info(
                "Temperature sensor %s at register %s: raw_value=%s, processed=%.1f°C",
                self._definition.key,
                self._definition.register_address,
                value,
                result,
            )
            return result

        return result


def create_sensor_class(definition: Any) -> type[DynamicSensor]:
    """Dynamically create a sensor class for the given definition."""
    return DynamicSensor
