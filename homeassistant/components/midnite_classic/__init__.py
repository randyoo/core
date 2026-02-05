"""The Midnite Classic integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
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
    Platform.BINARY_SENSOR,
    Platform.SELECT,
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

    return True


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
