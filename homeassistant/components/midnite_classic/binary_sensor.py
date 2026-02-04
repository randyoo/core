"""Support for Midnite Classic binary sensors.

These binary sensors extract specific bits from the Info Flags register (4130-4131)
without any additional modbus traffic - they simply reference bits from the
already-fetched data stored in the coordinator.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory  # type: ignore[attr-defined]
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .binary_sensors import INFO_FLAG_SENSORS
from .const import DOMAIN
from .coordinator import MidniteClassicCoordinator

_LOGGER = logging.getLogger(__name__)

# Bit position for each info flag (bits 0-15 are in register 4130, bits 16-31 in 4131)
INFO_FLAG_BITS = {
    # Low word (register 4130) - bits 0-15
    "info_flag_over_temperature": 0,
    "info_flag_eeprom_error": 1,
    "info_flag_serial_write_lock": 2,
    "info_flag_equalize_in_progress": 3,
    "info_flag_eq_mppt": 7,
    "info_flag_current_limit": 9,
    "info_flag_hyper_voc": 10,
    "info_flag_battery_temp_sensor_installed": 13,
    "info_flag_aux1_state_on": 14,
    "info_flag_aux2_state_on": 15,
    # High word (register 4131) - bits 16-31
    "info_flag_ground_fault": 16,
    "info_flag_over_current_protection": 17,
    "info_flag_arc_fault": 18,
    "info_flag_negative_battery_current": 19,
    "info_flag_extra_info_display": 21,
    "info_flag_watchdog_reset": 23,
    "info_flag_low_battery_voltage": 24,
    "info_flag_eq_done": 26,
    "info_flag_temp_comp_shorted": 27,
    "info_flag_input_shorted": 30,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Midnite Classic binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors: list[MidniteClassicBinarySensor] = []
    for definition in INFO_FLAG_SENSORS:
        sensor_class = create_binary_sensor_class(definition)
        sensors.append(sensor_class(coordinator, entry, definition))

    async_add_entities(sensors)


def create_binary_sensor_class(definition: Any) -> type[MidniteClassicBinarySensor]:
    """Dynamically create a binary sensor class for the given definition."""
    return type(
        f"MidniteClassicBinarySensor_{definition.key}",
        (MidniteClassicBinarySensor,),
        {},
    )


class MidniteClassicBinarySensor(
    CoordinatorEntity[MidniteClassicCoordinator], BinarySensorEntity
):
    """Binary sensor that extracts bits from Info Flags register."""

    def __init__(
        self,
        coordinator: MidniteClassicCoordinator,
        entry: ConfigEntry,
        definition: Any,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._definition = definition

        # Set basic attributes from definition
        self._attr_name = definition.name
        self._attr_unique_id = f"{entry.entry_id}_{definition.key}"

        # Set device class if defined
        self._set_device_class()

        # Set entity category if defined
        self._set_entity_category()

        # Set enabled_by_default flag if defined
        self._set_enabled_by_default()

    def _set_device_class(self) -> None:
        """Set the device class attribute."""
        if hasattr(self._definition, "device_class") and self._definition.device_class:
            device_class = self._definition.device_class
            self._attr_device_class = getattr(
                BinarySensorDeviceClass, device_class.upper(), None
            )

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
        return self.coordinator.update_device_info()

    @property
    def is_on(self) -> bool | None:
        """Return the state of the binary sensor (bit value).

        This extracts the specific bit from the combined 32-bit info flags value
        without any additional modbus traffic - it uses the already-fetched data.
        """
        if not self.coordinator.data or "data" not in self.coordinator.data:
            return None

        data = self.coordinator.data["data"]

        # Get the bit position for this sensor
        if self._definition.key not in INFO_FLAG_BITS:
            _LOGGER.warning("Unknown info flag key: %s", self._definition.key)
            return None

        bit_position = INFO_FLAG_BITS[self._definition.key]
        register_address = self._definition.register_address

        # Get the raw value from the appropriate register
        group_data = data.get(self._definition.register_group)
        if not group_data:
            return None

        raw_value = group_data.get(register_address)
        if raw_value is None:
            return None

        # Combine registers 4130 and 4131 into a 32-bit value
        # The low word (register 4130) contains bits 0-15
        # The high word (register 4131) contains bits 16-31
        low_word = group_data.get(4130, 0)
        high_word = group_data.get(4131, 0)
        combined_value = (high_word << 16) | low_word

        # Extract the specific bit
        bit_mask = 1 << bit_position
        return bool(combined_value & bit_mask)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available
