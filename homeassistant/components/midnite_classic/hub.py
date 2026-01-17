"""Support for Midnite Solar devices."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from pymodbus.client import ModbusTcpClient

_LOGGER = logging.getLogger(__name__)


class MidniteClassicHub:
    """Midnite Classic Hub for managing Modbus TCP connections."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize the hub."""
        self.host = host
        self.port = port
        # Use default RTU framer (not ASCII) - Midnite devices use standard Modbus TCP
        self._client = ModbusTcpClient(host=self.host, port=self.port)
        self._lock = threading.Lock()

    def is_still_connected(self) -> bool:
        """Check if the connection is still open."""
        with self._lock:
            return self._client.is_socket_open()

    def connect(self) -> bool | None:
        """Connect to the Modbus TCP server."""
        with self._lock:
            _LOGGER.info("Connecting to %s:%s", self.host, self.port)
            result = self._client.connect()
            _LOGGER.info("Connection result: %s", result)
            if result:
                _LOGGER.info("Successfully connected to device")
            else:
                _LOGGER.warning("Failed to connect to device")
            return result

    def disconnect(self) -> bool | None:
        """Disconnect from the Modbus TCP server."""
        with self._lock:
            if self._client.is_socket_open():
                _LOGGER.debug("Disconnecting from %s:%s", self.host, self.port)
                return self._client.close()
            return None

    def write_register(self, address: int, value: int) -> Any | None:
        """Write a register."""
        # Midnite devices use unit_id 1 by default
        with self._lock:
            return self._client.write_register(
                address=address - 1,  # Modbus addresses are 0-indexed
                value=value,
                # device_id=1,  # Removed - may cause issues with certain registers
            )

    def read_holding_registers(self, address: int, count: int = 1) -> Any | None:
        """Read holding registers with enhanced retry logic and debug logging."""
        _LOGGER.debug("Reading register %s (count=%s)", address, count)
        # Midnite devices use unit_id 1 by default

        max_retries = 5  # Increased from 3 to 5 for better reliability
        with self._lock:
            for attempt in range(max_retries):
                try:
                    # Ensure connection is active before reading
                    if not self._client.is_socket_open():
                        _LOGGER.debug(
                            "Connection closed, reconnecting before read attempt %s",
                            attempt + 1,
                        )
                        self.connect()
                        # Add a small delay after connect to allow device to stabilize
                        time.sleep(0.2)

                    result = self._client.read_holding_registers(
                        address=address - 1,  # Modbus addresses are 0-indexed
                        count=count,
                        # device_id=1,  # Removed - may cause issues with certain registers like 20492/20493
                    )
                    if result is not None and not result.isError():
                        _LOGGER.debug(
                            "Successfully read address %s: %s",
                            address,
                            result.registers,
                        )
                        return result
                    _LOGGER.warning(
                        "Attempt %s failed for address %s: %s",
                        attempt + 1,
                        address,
                        result,
                    )
                except OSError as e:
                    # Special handling for "Unable to decode request" errors
                    error_msg = str(e)
                    if (
                        "Unable to decode request" in error_msg
                        or "byte_count" in error_msg
                    ):
                        _LOGGER.debug(
                            "Attempt %s exception for address %s: %s",
                            attempt + 1,
                            address,
                            e,
                        )
                        _LOGGER.debug(
                            "This may indicate a Modbus protocol issue with this register range"
                        )
                        # Try to reset connection on protocol errors
                        if attempt < max_retries - 1:
                            _LOGGER.debug(
                                "Closing and reopening connection due to protocol error"
                            )
                            self.disconnect()
                    else:
                        _LOGGER.debug(
                            "Attempt %s exception for address %s: %s",
                            attempt + 1,
                            address,
                            e,
                        )

                    if attempt < max_retries - 1:
                        backoff_time = 0.2 * (
                            attempt + 1
                        )  # Increased exponential backoff
                        _LOGGER.debug(
                            "Waiting %ss before retry %s", backoff_time, attempt + 2
                        )
                        time.sleep(backoff_time)

            _LOGGER.warning(
                "All %s attempts failed for address %s, count=%s",
                max_retries,
                address,
                count,
            )
            return None
