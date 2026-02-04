"""Support for Midnite Classic button platform."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .button_definitions import BUTTON_DEFINITIONS
from .const import DOMAIN
from .coordinator import MidniteClassicCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Midnite Classic buttons."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    buttons = []
    for definition in BUTTON_DEFINITIONS:
        button_class = create_button_class(definition)
        buttons.append(button_class(coordinator, entry))

    async_add_entities(buttons)


def create_button_class(definition: Any):
    """Dynamically create a button class for the given definition."""

    class DynamicButton(CoordinatorEntity[MidniteClassicCoordinator], ButtonEntity):
        """Dynamic button based on definition."""

        def __init__(
            self, coordinator: MidniteClassicCoordinator, entry: ConfigEntry
        ) -> None:
            """Initialize the button."""
            super().__init__(coordinator)
            self._entry = entry
            self._definition = definition

            # Set basic attributes from definition
            self._attr_name = definition.name
            self._attr_unique_id = f"{entry.entry_id}_{definition.key}"
            if hasattr(definition, "icon"):
                self._attr_icon = definition.icon

        @property
        def device_info(self) -> DeviceInfo | None:
            """Return device info."""
            # Get device info from coordinator (includes MAC address from modbus)
            return self.coordinator.update_device_info()

        async def async_press(self) -> None:
            """Handle the button press."""
            # Compute the register value using write formula (lambda function)
            if callable(self._definition.write_formula):
                register_value = self._definition.write_formula(0)
            else:
                # Fallback for string formulas
                register_value = 0

            # Ensure register_value is an integer
            if isinstance(register_value, (int, float)):
                register_value_int = int(register_value)
            else:
                # Fallback - shouldn't happen with lambda formulas
                register_value_int = 0

            # Modbus registers are 16-bit, so mask with 0xFFFF to ensure value fits
            register_value_int = register_value_int & 0xFFFF

            # Check if writes are enabled before proceeding
            if not self.coordinator.api.writes_enabled:
                _LOGGER.info(
                    "Write protection enabled - button %s would write %s to register %s",
                    self._attr_name,
                    register_value_int,
                    self._definition.register_address,
                )
                return

            # Write to register
            try:
                await self.hass.async_add_executor_job(
                    self.coordinator.api.write_register,
                    int(self._definition.register_address),
                    register_value_int,
                )

                _LOGGER.info(
                    "Button %s wrote %s to register %s",
                    self._attr_name,
                    register_value_int,
                    self._definition.register_address,
                )

                # Force a refresh to show the updated value
                await self.coordinator.async_refresh()
            except (ValueError, TypeError) as exc:
                _LOGGER.error(
                    "Failed to write button %s to register %s: %s",
                    self._definition.key,
                    self._definition.register_address,
                    exc,
                )

    return DynamicButton
