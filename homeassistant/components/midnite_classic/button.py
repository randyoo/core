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
            # Check if writes are enabled before proceeding
            if not self.coordinator.api.writes_enabled:
                _LOGGER.warning(
                    "Button press for %s blocked by write protection", self._attr_name
                )
                return

            # Implement button press logic here

    return DynamicButton
