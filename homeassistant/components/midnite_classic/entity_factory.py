"""Factory functions for creating dynamic entities from definitions."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)


def get_device_class(device_class_str: str | None):
    """Convert string to SensorDeviceClass."""
    if not device_class_str:
        return None
    device_class_map = {
        "voltage": SensorDeviceClass.VOLTAGE,
        "current": SensorDeviceClass.CURRENT,
        "power": SensorDeviceClass.POWER,
        "energy": SensorDeviceClass.ENERGY,
        "temperature": SensorDeviceClass.TEMPERATURE,
        "duration": SensorDeviceClass.DURATION,
    }
    return device_class_map.get(device_class_str)


def get_state_class(state_class_str: str | None):
    """Convert string to SensorStateClass."""
    if not state_class_str:
        return None
    state_class_map = {
        "measurement": SensorStateClass.MEASUREMENT,
        "total_increasing": SensorStateClass.TOTAL_INCREASING,
    }
    return state_class_map.get(state_class_str)


def get_entity_category(category_str: str | None):
    """Convert string to EntityCategory."""
    if not category_str:
        return None
    category_map = {
        "diagnostic": EntityCategory.DIAGNOSTIC,
        "config": EntityCategory.CONFIG,
    }
    return category_map.get(category_str)


def evaluate_formula(
    formula: str, registers: dict[int, int], data: dict[str, Any]
) -> float | int:
    """Evaluate a formula using register values."""
    # Build context with register values
    context = {}
    for reg_num, value in registers.items():
        context[f"R{reg_num}"] = value
    try:
        return eval(formula, {"__builtins__": {}}, context)
    except Exception as exc:
        _LOGGER.error("Formula evaluation failed: %s - %s", formula, exc)
        raise ValueError("Formula evaluation failed: %s") from exc


class MidniteClassicSensor(CoordinatorEntity, SensorEntity):
    """Base class for dynamically created sensors."""

    def __init__(self, coordinator, entry, definition) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.definition = definition
        self._entry = entry
        self._attr_name = definition.name
        self._attr_unique_id = f"{entry.entry_id}_{definition.key}"
        self._attr_device_class = get_device_class(definition.device_class)
        self._attr_state_class = get_state_class(definition.state_class)
        self._attr_native_unit_of_measurement = definition.unit

        if hasattr(definition, "precision") and definition.precision is not None:
            self._attr_suggested_display_precision = definition.precision

        if hasattr(definition, "enabled_by_default"):
            self._attr_entity_registry_enabled_default = definition.enabled_by_default

        if hasattr(definition, "entity_category"):
            self._attr_entity_category = get_entity_category(definition.entity_category)

    @property
    def device_info(self):
        """Return device info with MAC address identifier."""
        return {
            "identifiers": {("midnite_classic", self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Midnite Solar",
        }

    @property
    def native_value(self) -> Any | None:
        """Return the state using the definition's formula."""
        data = self.coordinator.data.get("data", {}).get(self.definition.register_group)
        if not data:
            return None

        primary_value = data.get(self.definition.register_address)
        if primary_value is None:
            return None

        try:
            if callable(self.definition.formula):
                result = self.definition.formula(primary_value, data)
            else:
                # Build register map for formula evaluation
                register_map = {self.definition.register_address: primary_value}
                for reg in self.definition.secondary_registers:
                    if reg in data:
                        register_map[reg] = data[reg]
                result = evaluate_formula(self.definition.formula, register_map, data)

            # Validate min/max
            if hasattr(self.definition, "min_value") and result is not None:
                if result < self.definition.min_value:
                    return None

            if hasattr(self.definition, "max_value") and result is not None:
                if result > self.definition.max_value:
                    return None

            return result
        except Exception as exc:
            _LOGGER.error("Error calculating %s: %s", self.definition.key, exc)
            return None


def create_sensor_from_definition(definition, coordinator, entry):
    """Create a sensor from definition."""
    return MidniteClassicSensor(coordinator, entry, definition)


def create_entities_from_definitions(
    definitions: list[Any], coordinator: Any, entry: Any
) -> list[MidniteClassicSensor]:
    """Create multiple entities from definitions."""
    sensors = [d for d in definitions if d.entity_type == "sensor"]
    return [create_sensor_from_definition(defn, coordinator, entry) for defn in sensors]
