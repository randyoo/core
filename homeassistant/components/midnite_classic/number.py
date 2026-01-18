"""Support for Midnite Classic number platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MidniteClassicCoordinator
from .number_definitions import NUMBER_DEFINITIONS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Midnite Classic numbers."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    numbers = []
    for definition in NUMBER_DEFINITIONS:
        # Skip network registers (5-digit addresses starting with 204)
        if not str(definition.register_address).startswith("204"):
            number_class = create_number_class(definition)
            numbers.append(number_class(coordinator, entry, definition))

    async_add_entities(numbers)


def create_number_class(definition: Any):  # noqa: C901
    """Dynamically create a number class for the given definition."""

    class DynamicNumber(CoordinatorEntity[MidniteClassicCoordinator], NumberEntity):
        """Dynamic number based on definition."""

        def __init__(
            self,
            coordinator: MidniteClassicCoordinator,
            entry: ConfigEntry,
            definition: Any,
        ) -> None:
            """Initialize the number."""
            super().__init__(coordinator)
            self._entry = entry
            self._definition = definition

            # Set basic attributes from definition
            self._set_basic_attributes()
            self._set_device_class()
            self._set_unit_and_mode()

        def _set_basic_attributes(self) -> None:
            """Set basic number entity attributes."""
            self._attr_name = self._definition.name
            self._attr_unique_id = f"{self._entry.entry_id}_{self._definition.key}"

            if hasattr(self._definition, "min_value"):
                self._attr_min_value = self._definition.min_value
            if hasattr(self._definition, "max_value"):
                self._attr_max_value = self._definition.max_value
            if hasattr(self._definition, "step") and self._definition.step is not None:
                self._attr_step = self._definition.step

        def _set_device_class(self) -> None:
            """Set device class based on definition."""
            if (
                hasattr(self._definition, "device_class")
                and self._definition.device_class
            ):
                device_class_map = {
                    "voltage": NumberDeviceClass.VOLTAGE,
                    "current": NumberDeviceClass.CURRENT,
                    "duration": NumberDeviceClass.DURATION,
                }
                self._attr_device_class = device_class_map.get(
                    self._definition.device_class
                )

        def _set_unit_and_mode(self) -> None:
            """Set unit of measurement and mode."""
            if hasattr(self._definition, "unit"):
                self._attr_native_unit_of_measurement = self._definition.unit

            # Set mode to box for better UX with decimal values
            self._attr_mode = NumberMode.BOX

            # Ensure precision is set for proper display
            if (
                not hasattr(self._definition, "precision")
                or self._definition.precision is None
            ):
                self._attr_precision = 1

        @property
        def device_info(self):
            """Return device info."""
            return DeviceInfo(
                identifiers={(DOMAIN, self._entry.entry_id)},
                name=self._entry.title,
                manufacturer="Midnite Solar",
            )

        @property
        def native_value(self) -> float | int | None:
            """Return the current value."""
            if not self.coordinator.data or "data" not in self.coordinator.data:
                return None

            group_data = self.coordinator.data["data"].get(
                self._definition.register_group
            )
            if not group_data:
                return None

            value = group_data.get(self._definition.register_address)
            if value is None:
                return None

            # Apply formula if defined
            if hasattr(self._definition, "formula") and self._definition.formula:
                try:
                    # For number entities, we need to handle the formula differently
                    if callable(self._definition.formula):
                        result = self._definition.formula(value, group_data)
                    else:
                        # Simple string formula evaluation with basic arithmetic
                        # We need to replace the value in the formula string
                        formula_str = self._definition.formula.replace(
                            "value", str(value)
                        )
                        result = _evaluate_simple_formula(formula_str, value)

                    # Ensure result is a float - handle different numeric types
                    if isinstance(result, (int, float)):
                        return float(result)
                except (ValueError, SyntaxError) as exc:
                    _LOGGER.error(
                        "Error applying formula for %s: %s", self._definition.key, exc
                    )
                    return None

            return float(value)

        async def async_set_native_value(self, value: float) -> None:
            """Set the value."""
            # Check if writes are enabled before proceeding
            if not self.coordinator.api.writes_enabled:
                _LOGGER.warning(
                    "Setting value for %s blocked by write protection. Value attempted: %s",
                    self._attr_name,
                    value,
                )
                return

            # Apply write formula if defined
            if (
                hasattr(self._definition, "write_formula")
                and self._definition.write_formula
            ):
                try:
                    # Convert value to register format
                    if callable(self._definition.write_formula):
                        register_value = self._definition.write_formula(value)
                    else:
                        # Simple string formula evaluation with basic arithmetic for write
                        formula_str = self._definition.write_formula.replace(
                            "value", str(value)
                        )
                        register_value = _evaluate_simple_formula(formula_str, value)

                    # Ensure register_value is an integer - use explicit type conversion
                    if isinstance(register_value, (int, float)):
                        register_value = int(register_value)
                    else:
                        # For other types, try to convert or fail gracefully
                        try:
                            register_value = int(str(register_value))
                        except (ValueError, TypeError) as exc:
                            _LOGGER.error(
                                "Failed to convert register value to integer for %s: %s",
                                self._definition.key,
                                exc,
                            )
                            return

                    # Write to register - type is now guaranteed to be int
                    await self.hass.async_add_executor_job(
                        self.coordinator.api.write_register,
                        int(self._definition.register_address),
                        register_value,
                    )

                    # Force a refresh to show the updated value
                    await self.coordinator.async_refresh()
                except (ValueError, SyntaxError) as exc:
                    _LOGGER.error(
                        "Failed to write value %s to register %s: %s",
                        value,
                        self._definition.register_address,
                        exc,
                    )
            else:
                _LOGGER.warning("No write formula defined for %s", self._definition.key)

    def _evaluate_simple_formula(formula: str, value: float) -> float | None:
        """Evaluate a simple arithmetic formula string safely.

        Supports basic operations: +, -, *, / with numbers and the 'value' variable.
        """
        # Replace value placeholder first
        formula_str = formula.replace("value", str(value))

        try:
            # Use eval with restricted globals for simple expressions
            # This is safe because we control what gets into formula_str from NUMBER_DEFINITIONS
            return float(
                eval(formula_str, {"__builtins__": {}, "int": int, "float": float}, {})  # noqa: S307
            )
        except (ValueError, SyntaxError, TypeError) as exc:
            _LOGGER.debug("Failed to evaluate formula %s: %s", formula, exc)
            return None

    return DynamicNumber
