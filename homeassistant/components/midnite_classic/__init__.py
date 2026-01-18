"""The Midnite Classic integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import MidniteClassicCoordinator

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
]

type MidniteClassicConfigEntry = ConfigEntry[MidniteClassicCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: MidniteClassicConfigEntry
) -> bool:
    """Set up Midnite Classic from a config entry."""
    coordinator = MidniteClassicCoordinator(
        hass,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        config_entry=entry,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Failed to connect to Midnite Classic device: %s", err)
        raise ConfigEntryNotReady(
            "Could not connect to Midnite Classic device"
        ) from err

    # Store the coordinator in runtime_data
    entry.runtime_data = coordinator

    # Also store in hass.data for backward compatibility if needed
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    entry.add_update_listener(update_listener)

    return True


async def async_get_options_flow(
    config_entry: MidniteClassicConfigEntry,
) -> MidniteClassicOptionsFlow:
    """Create the options flow."""
    return MidniteClassicOptionsFlow(config_entry)


class MidniteClassicOptionsFlow(ConfigFlow):
    """Handle options flow for Midnite Classic."""

    def __init__(self, config_entry: MidniteClassicConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update the config entry with new options
            self.hass.config_entries.async_update_entry(
                self.config_entry, options={**self.config_entry.options, **user_input}
            )
            # Reload the integration to apply changes
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data={})

        # Get current options
        current_options = self.config_entry.options

        # Create form with current values
        data_schema = vol.Schema(
            {
                vol.Optional(
                    "enable_writes", default=current_options.get("enable_writes", False)
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )


async def async_unload_entry(
    hass: HomeAssistant, entry: MidniteClassicConfigEntry
) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, _PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        if coordinator is not None:
            await coordinator.shutdown()

    return unload_ok


async def update_listener(
    hass: HomeAssistant, entry: MidniteClassicConfigEntry
) -> None:
    """Handle options updates."""
    _LOGGER.info("Options updated, reloading Midnite Classic integration")

    await hass.config_entries.async_reload(entry.entry_id)
