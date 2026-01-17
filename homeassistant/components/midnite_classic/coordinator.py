"""Define the Midnite Classic Device Update Coordinator."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

# import pymodbus
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .button_definitions import BUTTON_DEFINITIONS
from .const import DOMAIN

try:
    from .const import CONF_SCAN_INTERVAL
except ImportError:
    CONF_SCAN_INTERVAL = "scan_interval"
from .hub import MidniteClassicHub
from .number_definitions import NUMBER_DEFINITIONS
from .select_definitions import SELECT_DEFINITIONS
from .sensor_definitions import SENSOR_DEFINITIONS
from .text_definitions import TEXT_DEFINITIONS

_LOGGER = logging.getLogger(__name__)


class MidniteClassicCoordinator(DataUpdateCoordinator):
    """Gather data for the Midnite Classic device."""

    api: MidniteClassicHub

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        interval: int = 15,
        config_entry=None,
    ) -> None:
        """Initialize Update Coordinator."""

        # Get scan interval from options if available, otherwise use default
        if config_entry and hasattr(config_entry, "options"):
            interval = config_entry.options.get(CONF_SCAN_INTERVAL, interval)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
            config_entry=config_entry,
        )
        self.api = MidniteClassicHub(host, port)
        self.interval = interval
        self.device_info: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all device and sensor data from api."""

        unavailable_entities: dict[str, list[int]] = {}

        # Ensure connection is active
        if not self.api.is_still_connected():
            _LOGGER.debug("Connection not active, attempting to reconnect")
            try:
                await self.hass.async_add_executor_job(self.api.connect)
                # Add delay after connect to allow device to respond
                await asyncio.sleep(0.5)
            except Exception as e:
                _LOGGER.error("Failed to connect: %s", e)
                raise UpdateFailed("Cannot connect to device: %s") from e

        # Test connection with a simple read before proceeding
        # Try multiple registers to handle temporary communication issues
        try:
            _LOGGER.debug("Testing connection by reading UNIT_ID register (4101)")
            test_result = await self.hass.async_add_executor_job(
                self.api.read_holding_registers, 4101, 1
            )
            if test_result is None or test_result.isError():
                _LOGGER.warning(
                    "Connection test failed on UNIT_ID. Trying alternative register"
                )
                # Try a different register that might be more stable (4-digit address)
                _LOGGER.debug("Trying alternative register 4102")
                test_result = await self.hass.async_add_executor_job(
                    self.api.read_holding_registers, 4102, 1
                )
                if test_result is None or test_result.isError():
                    raise UpdateFailed("Device not responding to connection tests")

            unit_id = test_result.registers[0] if test_result.registers else None
            _LOGGER.debug("Connection test successful. UNIT_ID: %s", unit_id)
        except OSError:
            _LOGGER.exception("Connection test failed with exception")
            # Try to reconnect once more with detailed logging
            try:
                await self.hass.async_add_executor_job(self.api.disconnect)
                await asyncio.sleep(0.3)  # Brief pause before reconnect
                await self.hass.async_add_executor_job(self.api.connect)
                await asyncio.sleep(0.5)  # Allow device to respond after reconnect

                _LOGGER.debug(
                    "Testing connection again after reconnect (register 4101)"
                )
                test_result = await self.hass.async_add_executor_job(
                    self.api.read_holding_registers, 4101, 1
                )
                if test_result is None or test_result.isError():
                    _LOGGER.error(
                        "Connection test still failing after reconnect. Result: %s",
                        test_result,
                    )
                    raise UpdateFailed("Device not responding after reconnect attempt")

                unit_id = test_result.registers[0] if test_result.registers else None
                _LOGGER.debug("Reconnect successful. UNIT_ID: %s", unit_id)
            except OSError as exc2:
                _LOGGER.exception("Reconnect failed")
                raise UpdateFailed("Cannot communicate with device: %s") from exc2

        all_definitions = (
            SENSOR_DEFINITIONS
            + BUTTON_DEFINITIONS
            + NUMBER_DEFINITIONS
            + SELECT_DEFINITIONS
            + TEXT_DEFINITIONS
        )

        # Group registers by register_group
        register_groups: dict[str, set[int]] = {}
        for definition in all_definitions:
            group_name = definition.register_group
            if group_name not in register_groups:
                register_groups[group_name] = set()
            register_groups[group_name].add(definition.register_address)
            register_groups[group_name].update(definition.secondary_registers)

        # Read each register group
        data: dict[str, dict[int, Any]] = {}

        for group_name, registers in register_groups.items():
            _LOGGER.debug(
                "Reading register group %s: %s", group_name, sorted(registers)
            )
            result_data = await self._read_register_group(list(registers))
            if result_data:
                data[group_name] = result_data
            else:
                unavailable_entities[group_name] = list(registers)

        return {
            "data": data,
            "availability": unavailable_entities,
        }

    async def _read_register_group(self, registers: list[int]) -> dict[int, Any] | None:
        """Read a group of registers with enhanced debug logging."""
        if not registers:
            return None

        # Sort and deduplicate registers
        sorted_regs = sorted(set(registers))
        result_data = {}
        failed_registers = []

        for reg in sorted_regs:

            async def _read_single_register(current_reg: int) -> None:
                """Read a single register."""
                result = await self.hass.async_add_executor_job(
                    self.api.read_holding_registers, current_reg, 1
                )
                if result is not None and not result.isError():
                    value = result.registers[0]
                    nonlocal result_data
                    result_data[current_reg] = value
                    _LOGGER.debug(
                        "Successfully read register %s: %s", current_reg, value
                    )
                else:
                    _LOGGER.warning("Failed to read register %s", current_reg)

            try:
                _LOGGER.debug("Reading register %s", reg)
                await _read_single_register(reg)
            except OSError:
                _LOGGER.warning("Exception reading register %s", reg, exc_info=True)
                failed_registers.append(reg)

        if failed_registers:
            _LOGGER.debug("Failed to read registers: %s", failed_registers)

        return result_data if result_data else None

    def get_register_value(self, address: int) -> int | None:
        """Get a specific register value from the last update."""
        if self.data is None or "data" not in self.data:
            return None

        for registers_data in self.data["data"].values():
            if address in registers_data:
                return registers_data.get(address)

        return None

    def get_32bit_value(self, low_address: int, high_address: int) -> int | None:
        """Get a 32-bit value from two registers."""
        if self.data is None or "data" not in self.data:
            return None

        for registers_data in self.data["data"].values():
            low_value = registers_data.get(low_address)
            high_value = registers_data.get(high_address)
            if low_value is not None and high_value is not None:
                return (high_value << 16) | low_value

        return None

    async def shutdown(self) -> None:
        """Shutdown the coordinator and disconnect from device."""
        _LOGGER.debug("Shutting down Midnite Classic coordinator")
        if hasattr(self, "api") and self.api is not None:
            try:
                await self.hass.async_add_executor_job(self.api.disconnect)
                _LOGGER.debug("Successfully disconnected from device")
            except OSError as e:
                _LOGGER.warning("Error during disconnect: %s", e)
