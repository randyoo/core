"""Config flow for the Midnite Classic integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from .const import DEFAULT_PORT, DOMAIN

# Add scan interval constant if not already present
try:
    from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
except ImportError:
    CONF_SCAN_INTERVAL = "scan_interval"
    DEFAULT_SCAN_INTERVAL = 15

_LOGGER = logging.getLogger(__name__)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required("enable_writes", default=False): bool,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)


class MidniteClassicConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Midnite Classic."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._discovery_info: DhcpServiceInfo | None = None
        _LOGGER.info("MidniteClassicConfigFlow initialized")

    @property
    def discovery_info(self) -> DhcpServiceInfo | None:
        """Return the discovery info."""
        return self._discovery_info

    @discovery_info.setter
    def discovery_info(self, value: DhcpServiceInfo | None) -> None:
        """Set the discovery info."""
        self._discovery_info = value

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step (manual or DHCP discovery)."""
        _LOGGER.info("Async_step_user CALLED")
        _LOGGER.info("User_input: %s", user_input)

        # Check if we came from DHCP discovery
        discovered = hasattr(self, "discovery_info") and self.discovery_info is not None
        if discovered:
            assert self.discovery_info is not None  # For type checking
            _LOGGER.info("✓ Called from DHCP DISCOVERY")
            _LOGGER.info("  MAC: %s", self.discovery_info.macaddress)
            _LOGGER.info("  IP: %s", self.discovery_info.ip)
        else:
            _LOGGER.info("✓ Called from MANUAL entry")

        errors: dict[str, str] = {}

        if user_input is not None:
            # If triggered by discovery, user_input may only contain confirmation
            # If triggered manually, user_input contains full form data

            # For DHCP discovery, pre-fill the host and port from discovery info
            if discovered and CONF_HOST not in user_input:
                assert self.discovery_info is not None  # For type checking
                _LOGGER.debug(
                    "Pre-filling IP address from DHCP discovery: %s",
                    self.discovery_info.ip,
                )
                user_input[CONF_HOST] = self.discovery_info.ip
                user_input[CONF_PORT] = DEFAULT_PORT

            # Check for duplicate entries
            self._async_abort_entries_match(
                {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input.get(CONF_PORT, DEFAULT_PORT),
                }
            )

            if not errors:
                # Determine title based on discovery or manual entry
                if discovered and self.discovery_info:
                    title = f"Midnite Classic @ {user_input[CONF_HOST]}"
                else:
                    title = f"Midnite Classic @ {user_input[CONF_HOST]}"

                # Create entry with data and options
                entry_data = {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input.get(CONF_PORT, DEFAULT_PORT),
                }
                entry_options = {}

                if "enable_writes" in user_input:
                    entry_options["enable_writes"] = user_input["enable_writes"]

                if CONF_SCAN_INTERVAL in user_input:
                    entry_options[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]

                return self.async_create_entry(
                    title=title,
                    data=entry_data,
                    options=entry_options,
                )

        # Show appropriate form based on discovery status
        if discovered and self.discovery_info:
            assert self.discovery_info is not None  # For type checking
            _LOGGER.info("SHOWING DISCOVERY CONFIRMATION FORM")
            _LOGGER.info("Device IP: %s", self.discovery_info.ip)
            _LOGGER.info("User should see a 'Discovered' card in UI")

            data_schema = vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self.discovery_info.ip): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): int,
                }
            )

            return self.async_show_form(
                step_id="user",
                data_schema=data_schema,
                description_placeholders={
                    "ip": self.discovery_info.ip,
                    "mac": self.discovery_info.macaddress,
                },
                errors=errors,
            )

        _LOGGER.info("SHOWING MANUAL CONFIGURATION FORM")
        _LOGGER.info("User should see full config form in UI")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): int,
                    vol.Optional("enable_writes", default=False): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        """Handle DHCP discovery."""
        _LOGGER.info("DHCP DISCOVERY TRIGGERED!")
        _LOGGER.info("Device IP: %s", discovery_info.ip)
        _LOGGER.info("MAC Address: %s", discovery_info.macaddress)

        # Set unique ID to prevent duplicates
        await self.async_set_unique_id(discovery_info.macaddress)
        self._abort_if_unique_id_configured()

        # Store discovery info for user confirmation
        self._discovery_info = discovery_info

        # Show user confirmation with pre-filled IP and port
        return self.async_show_form(
            step_id="user",
            description_placeholders={
                "ip": discovery_info.ip,
                "mac": discovery_info.macaddress,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow."""
        return MidniteClassicOptionsFlowHandler(config_entry)


class MidniteClassicOptionsFlowHandler(OptionsFlowWithReload):
    """Handle options flow for Midnite Classic."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self._config_entry = config_entry

    @property
    def config_entry(self) -> ConfigEntry:
        """Return the config entry."""
        return self._config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )
