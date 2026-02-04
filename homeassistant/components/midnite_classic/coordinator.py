"""Define the Midnite Classic Device Update Coordinator."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

# import pymodbus
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceInfo,
    format_mac,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .button_definitions import BUTTON_DEFINITIONS
from .const import DEVICE_TYPES, DOMAIN

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

type MidniteClassicConfigEntry = ConfigEntry[MidniteClassicCoordinator]


def parse_mac_from_registers(registers: dict[int, int]) -> str | None:
    """Parse MAC address from modbus registers 4106-4108.

    Register 4106 contains the first 2 bytes (bytes 4-5 of MAC)
    Register 4107 contains the middle 2 bytes (bytes 2-3 of MAC)
    Register 4108 contains the last 2 bytes (bytes 0-1 of MAC)

    The bytes are in big-endian order within each register.
    """
    if not registers:
        return None

    reg_4106 = registers.get(4106)
    reg_4107 = registers.get(4107)
    reg_4108 = registers.get(4108)

    if reg_4106 is None or reg_4107 is None or reg_4108 is None:
        return None

    # Extract bytes from registers
    # Register format: high byte first, low byte second
    # Reg 4106: bytes 4-5 (most significant)
    # Reg 4107: bytes 2-3
    # Reg 4108: bytes 0-1 (least significant)

    part2 = reg_4107
    part3 = reg_4108

    mac_bytes = [
        (part3 >> 8) & 0xFF,
        part3 & 0xFF,
        (part2 >> 8) & 0xFF,
        part2 & 0xFF,
        (reg_4106 >> 8) & 0xFF,
        reg_4106 & 0xFF,
    ]

    # Format as MAC address with colons
    return ":".join(f"{byte:02X}" for byte in mac_bytes)


class MidniteClassicCoordinator(DataUpdateCoordinator):
    """Gather data for the Midnite Classic device."""

    api: MidniteClassicHub
    config_entry: MidniteClassicConfigEntry

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
        # Get writes_enabled from config entry options
        writes_enabled = False
        if config_entry and hasattr(config_entry, "options"):
            writes_enabled = config_entry.options.get("enable_writes", False)
        self.api = MidniteClassicHub(host, port, writes_enabled)
        self.interval = interval
        self.device_info: dict[str, Any] = {}
        # MAC address read from modbus registers (4106-4108)
        self.mac_address: str | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all device and sensor data from api."""

        unavailable_entities: dict[str, list[int]] = {}

        # Ensure connection is active - be more aggressive about reconnecting
        if not self.api.is_still_connected():
            _LOGGER.debug("Connection not active, attempting to reconnect")
            try:
                await self.hass.async_add_executor_job(self.api.disconnect)
                await asyncio.sleep(0.2)  # Brief pause before reconnect
                success = await self.hass.async_add_executor_job(self.api.connect)
                if not success:
                    self._raise_connection_failed()

                # Add delay after connect to allow device to respond
                await asyncio.sleep(0.5)
            except (TimeoutError, ConnectionError) as e:
                _LOGGER.error("Failed to connect: %s", e)
                self._raise_connection_failed_with_error(e)
            except OSError as e:
                _LOGGER.error("Failed to connect: %s", e)
                self._raise_connection_failed_with_error(e)

        # Test connection with a simple read before proceeding
        # Try multiple registers to handle temporary communication issues
        test_result = None
        try:
            _LOGGER.debug("Testing connection by reading UNIT_ID register (4101)")
            test_result = await self.hass.async_add_executor_job(
                self.api.read_holding_registers, 4101, 1
            )
            if test_result is not None and not test_result.isError():
                unit_id = test_result.registers[0] if test_result.registers else None
                _LOGGER.debug("Connection test successful. UNIT_ID: %s", unit_id)
            else:
                _LOGGER.warning(
                    "Connection test failed on UNIT_ID (result: %s). Trying alternative register",
                    test_result,
                )
                # Try a different register that might be more stable
                _LOGGER.debug("Trying alternative register 4102")
                test_result = await self.hass.async_add_executor_job(
                    self.api.read_holding_registers, 4102, 1
                )
                if test_result is None or test_result.isError():
                    # Try one more time with a different approach - disconnect and reconnect
                    _LOGGER.warning(
                        "Connection tests failing, attempting full reconnect cycle"
                    )
                    try:
                        await self.hass.async_add_executor_job(self.api.disconnect)
                        await asyncio.sleep(0.3)  # Brief pause before reconnect
                        success = await self.hass.async_add_executor_job(
                            self.api.connect
                        )
                        if not success:
                            self._raise_connection_failed()

                        await asyncio.sleep(
                            0.5
                        )  # Allow device to respond after reconnect

                        _LOGGER.debug(
                            "Testing connection again after full reconnect (register 4101)"
                        )
                        test_result = await self.hass.async_add_executor_job(
                            self.api.read_holding_registers, 4101, 1
                        )
                        if test_result is None or test_result.isError():
                            _LOGGER.error(
                                "Connection test still failing after reconnect. Result: %s",
                                test_result,
                            )
                            self._raise_device_not_responding()
                    except (OSError, TimeoutError, ConnectionError) as exc2:
                        _LOGGER.exception("Reconnect and retest failed")
                        self._raise_communication_failed(exc2)

        except OSError:
            _LOGGER.exception("Connection test failed with exception")
            # Try one more time with a clean connection
            try:
                await self.hass.async_add_executor_job(self.api.disconnect)
                await asyncio.sleep(0.3)  # Brief pause before reconnect
                success = await self.hass.async_add_executor_job(self.api.connect)
                if not success:
                    self._raise_connection_failed()

                await asyncio.sleep(0.5)  # Allow device to respond after reconnect

                _LOGGER.debug(
                    "Testing connection again after exception recovery (register 4101)"
                )
                test_result = await self.hass.async_add_executor_job(
                    self.api.read_holding_registers, 4101, 1
                )
                if test_result is None or test_result.isError():
                    _LOGGER.error(
                        "Connection test still failing after exception recovery. Result: %s",
                        test_result,
                    )
                    self._raise_device_not_responding_recovery()

            except (OSError, TimeoutError, ConnectionError) as exc2:
                _LOGGER.exception("Final reconnect failed")
                self._raise_communication_failed(exc2)

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

        # Extract MAC address from modbus registers (4106-4108) if available
        if data:
            device_info_data = data.get("device_info", {})
            if mac := parse_mac_from_registers(device_info_data):
                self.mac_address = mac
                _LOGGER.debug("MAC address read from device: %s", mac)

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

    def _raise_connection_failed(self) -> None:
        """Raise UpdateFailed for connection failure."""
        raise UpdateFailed("Cannot connect to device")

    def _raise_connection_failed_with_error(self, error: Exception) -> None:
        """Raise UpdateFailed for connection failure with error details."""
        raise UpdateFailed("Cannot connect to device: %s") from error

    def _raise_device_not_responding(self) -> None:
        """Raise UpdateFailed when device is not responding to connection tests."""
        raise UpdateFailed("Device not responding to connection tests")

    def _raise_device_not_responding_recovery(self) -> None:
        """Raise UpdateFailed when device is not responding after recovery attempt."""
        raise UpdateFailed("Device not responding after recovery attempt")

    def _raise_communication_failed(self, error: Exception) -> None:
        """Raise UpdateFailed for communication failure with error details."""
        raise UpdateFailed("Cannot communicate with device: %s") from error

    async def shutdown(self) -> None:
        """Shutdown the coordinator and disconnect from device."""
        _LOGGER.debug("Shutting down Midnite Classic coordinator")
        if hasattr(self, "api") and self.api is not None:
            try:
                await self.hass.async_add_executor_job(self.api.disconnect)
                _LOGGER.debug("Successfully disconnected from device")
            except OSError as e:
                _LOGGER.warning("Error during disconnect: %s", e)

    def update_device_info(self) -> DeviceInfo:
        """Update device info with MAC address if available."""
        # Build identifiers
        identifiers = {(DOMAIN, self.config_entry.entry_id)}

        # Get model and firmware from device_info data
        model = None
        sw_version = None
        hw_version = None

        if self.data and "data" in self.data:
            device_data = self.data.get("data", {})
            if device_info_data := device_data.get("device_info"):
                # Get the device type value from register 4101
                unit_id_value = device_info_data.get(4101)
                if unit_id_value is not None:
                    device_type = unit_id_value & 0xFF  # Get LSB (unit type)
                    model = DEVICE_TYPES.get(device_type, f"Unknown ({device_type})")

                # Get firmware version from registers 4102-4103
                fw_year = device_info_data.get(4102)
                fw_register = device_info_data.get(4103)
                if fw_year is not None and fw_register is not None:
                    fw_month = (fw_register >> 8) & 0xFF  # Extract high byte (MSB)
                    fw_day = fw_register & 0xFF  # Extract low byte (LSB)
                    sw_version = f"{fw_year}-{fw_month:02d}-{fw_day:02d}"

                # Get PCB revision from UNIT_ID register bits 8-15
                pcb_rev = (unit_id_value >> 8) & 0xFF if unit_id_value else None
                if pcb_rev is not None:
                    hw_version = f"Rev {pcb_rev}"

        # Build device info
        device_info = DeviceInfo(
            identifiers=identifiers,
            name=self.config_entry.title,
            manufacturer="Midnite Solar",
        )

        # Add MAC address from modbus registers if available
        if self.mac_address:
            device_info["connections"] = {
                (CONNECTION_NETWORK_MAC, format_mac(self.mac_address))
            }

        # Set optional attributes
        if model:
            device_info["model"] = model
        if sw_version:
            device_info["sw_version"] = sw_version
        if hw_version:
            device_info["hw_version"] = hw_version

        return device_info
