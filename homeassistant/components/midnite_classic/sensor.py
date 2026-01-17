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
        # Try to get model information from the device_type sensor if available
        model = None
        sw_version = None
        hw_version = None
        if self.coordinator.data and "data" in self.coordinator.data:
            device_info_data = self.coordinator.data["data"].get("device_info")
            if device_info_data:
                # Get the device type value from register 4101
                unit_id_value = device_info_data.get(4101)
                if unit_id_value is not None:
                    device_type = unit_id_value & 0xFF  # Get LSB (unit type)
                    model = DEVICE_TYPES.get(device_type, f"Unknown ({device_type})")

                # Get firmware version from registers 4102-4103
                fw_year = device_info_data.get(4102)
                fw_register = device_info_data.get(4103)
                if fw_year is not None and fw_register is not None:
                    fw_month = (fw_register >> 8) & 0xFF  # Extract high byte (MSB)
                    fw_day = fw_register & 0xFF  # Extract low byte (LSB)
                    sw_version = f"{fw_year}-{fw_month:02d}-{fw_day:02d}"

                # Get PCB revision from UNIT_ID register bits 8-15
                pcb_rev = (unit_id_value >> 8) & 0xFF if unit_id_value else None
                if pcb_rev is not None:
                    hw_version = f"Rev {pcb_rev}"

        # Build identifiers with device ID if available
        identifiers = {(DOMAIN, self._entry.entry_id)}

        # If we can get a proper device ID from registers 4111-4112, use it
        if device_info_data:
            device_id_lsw = device_info_data.get(4111)
            device_id_msw = device_info_data.get(4112)
            if device_id_lsw is not None and device_id_msw is not None:
                device_id = (device_id_msw << 16) | device_id_lsw
                identifiers = {(DOMAIN, str(device_id))}

        return {
            "identifiers": identifiers,
            "name": self._entry.title,
            "manufacturer": "Midnite Solar",
            "model": model,
            "sw_version": sw_version,
            "hw_version": hw_version,
        }

    @property
    def native_value(  # pylint: disable=hass-return-type
        self,
    ) -> Any | None:
        """Return the state of the sensor."""
        if not self.coordinator.data or "data" not in self.coordinator.data:
            return None

        group_data = self.coordinator.data["data"].get(self._definition.register_group)
        if not group_data:
            return None

        value = group_data.get(self._definition.register_address)
        if value is None:
            return None

        # Apply formula if defined (string-based only for safety)
        if hasattr(self._definition, "formula") and self._definition.formula:
            result = self._apply_formula(value, group_data)
            if result is not None:
                return result

        # Apply temperature helper for temperature sensors without formulas
        if self._definition.key in TEMPERATURE_SENSOR_KEYS and isinstance(
            value, (int, float)
        ):
            return _TEMP_HELPER.process_temperature(
                self._definition.key, value, self._definition.register_address
            )

        return value

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
            return _TEMP_HELPER.process_temperature(
                self._definition.key,
                result,
                self._definition.register_address,
            )

        return result


def create_sensor_class(definition: Any) -> type[DynamicSensor]:
    """Dynamically create a sensor class for the given definition."""
    return DynamicSensor
