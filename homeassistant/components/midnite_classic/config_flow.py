"""Config flow for the Midnite Classic integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from .const import DEFAULT_PORT, DOMAIN

# Add scan interval constant if not already present
try:
    from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
except ImportError:
    CONF_SCAN_INTERVAL = "scan_interval"
    DEFAULT_SCAN_INTERVAL = 15

_LOGGER = logging.getLogger(__name__)


class MidniteClassicConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Midnite Classic."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self.discovery_info: DhcpServiceInfo | None = None

    async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        """Handle DHCP discovery."""
        _LOGGER.info("DHCP DISCOVERY TRIGGERED!")
        _LOGGER.info("Device IP: %s", discovery_info.ip)
        _LOGGER.info("MAC Address: %s", discovery_info.macaddress)

        # Format the MAC address properly for unique ID using Home Assistant's standard format
        formatted_mac = format_mac(discovery_info.macaddress)

        # Set unique ID to prevent duplicate setups
        await self.async_set_unique_id(formatted_mac, raise_on_progress=False)

        # Abort if device is already configured (this will also update IP if it changed)
        existing_entries = self._async_current_entries()
        for entry in existing_entries:
            if entry.unique_id == formatted_mac:
                _LOGGER.warning(
                    "Device with MAC %s at %s is already configured as '%s'. "
                    "Skipping discovery",
                    discovery_info.macaddress,
                    discovery_info.ip,
                    entry.title,
                )
                return self.async_abort(reason="already_configured")

        # Update IP if device was previously configured with a different IP
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.ip})

        # Store discovery info for user confirmation
        self.discovery_info = discovery_info

        # Set initial title placeholder - will be updated with model if successful
        self.context["title_placeholders"] = {"name": "Midnite Classic"}

        # Try to read device model from the device for better identification in UI
        try:
            _LOGGER.warning(
                "Attempting to read device model from %s", discovery_info.ip
            )
            # Note: Device model reading is disabled until pymodbus is added as a requirement
            # client = ModbusTcpClient(discovery_info.ip, port=DEFAULT_PORT)
            # connected = await self.hass.async_add_executor_job(client.connect)
            # if connected:
            #     _LOGGER.warning(
            #         f"Successfully connected to {discovery_info.ip}, reading model info..."
            #     )
            #     # Read UNIT_ID register to get device type
            #     result = await self.hass.async_add_executor_job(
            #         lambda: client.read_holding_registers(address=4100, count=2)
            #     )
            #     client.close()
            #
            #     if result and not result.isError():
            #         # Register 4101 contains device type in LSB
            #         unit_id = result.registers[0] if len(result.registers) > 0 else None
            #         if unit_id is not None:
            #             from .const import DEVICE_TYPES
            #
            #             device_type = unit_id & 0xFF  # Get LSB (unit type)
            #             model_name = DEVICE_TYPES.get(
            #                 device_type, f"Midnite Device ({device_type})"
            #             )
            #             _LOGGER.warning(f"Discovered device model: {model_name}")
            #             # Set the model as the name for badge display
            #             self.context["title_placeholders"]["name"] = model_name
            #         else:
            #             _LOGGER.warning(
            #                 "Could not read UNIT_ID register - result.registers is empty"
            #             )
            #     else:
            #         _LOGGER.warning(
            #             f"Failed to read device registers: {result}. IsError={result.isError() if result else 'N/A'}"
            #         )
            # else:
            #     _LOGGER.warning(
            #         f"Could not connect to device at {discovery_info.ip} for model identification"
            #     )
        except OSError:
            _LOGGER.warning("Error reading device model during discovery")

        # Log the final title placeholder for debugging
        _LOGGER.warning(
            "Discovery badge will display: '%s'",
            self.context["title_placeholders"]["name"],
        )

        # Show user confirmation with pre-filled IP and port
        return self.async_show_form(
            step_id="user",
            description_placeholders={
                "ip": discovery_info.ip,
                "mac": discovery_info.macaddress,
            },
        )

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

            # Test connection (disabled until pymodbus is added as a requirement)
            # import pymodbus
            #
            # _LOGGER.info(f"PyModbus version: {pymodbus.__version__}")
            # sig = inspect.signature(ModbusTcpClient.read_holding_registers)
            # _LOGGER.info(f"read_holding_registers signature: {sig}")
            #
            # client = ModbusTcpClient(user_input[CONF_HOST], port=user_input[CONF_PORT])
            # try:
            #     connected = await self.hass.async_add_executor_job(client.connect)
            #     if not connected:
            #         errors["base"] = "cannot_connect"
            #     else:
            #         # Try to read a register to verify communication
            #         result = await self.hass.async_add_executor_job(
            #             lambda: client.read_holding_registers(address=4100, count=1)
            #         )
            #         if result.isError():
            #             errors["base"] = "cannot_read"
            #
            #     client.close()
            # except Exception as ex:
            #     _LOGGER.exception("Unexpected exception during connection test")
            #     errors["base"] = "unknown"

            if not errors:
                # Determine title based on discovery or manual entry
                if discovered and self.discovery_info:
                    title = f"Midnite Classic @ {user_input[CONF_HOST]}"
                else:
                    title = f"Midnite Classic @ {user_input[CONF_HOST]}"

                # Separate scan_interval from data to store in options
                entry_data = {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input.get(CONF_PORT, DEFAULT_PORT),
                }
                entry_options = {}
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
            # For DHCP discovery, show a confirmation dialog with device details
            _LOGGER.info("SHOWING DISCOVERY CONFIRMATION FORM")
            _LOGGER.info("Device IP: %s", self.discovery_info.ip)
            _LOGGER.info("User should see a 'Discovered' card in UI")

            # Create data schema with pre-filled values for DHCP discovery
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self.discovery_info.ip): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): int,
                }
            )

            self.async_show_form(
                step_id="user",
                data_schema=data_schema,
                description_placeholders={
                    "ip": self.discovery_info.ip,
                    "mac": self.discovery_info.macaddress,
                },
                errors=errors,
            )

        # For manual entry, show the full configuration form
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
                }
            ),
            errors=errors,
        )
