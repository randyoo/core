"""Support for Midnite Solar devices."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusException

_LOGGER = logging.getLogger(__name__)


class MidniteClassicHub:
    """Midnite Classic Hub for managing Modbus TCP connections."""

    def __init__(self, host: str, port: int, writes_enabled: bool = False) -> None:
        """Initialize the hub."""
        self.host = host
        self.port = port
        self._writes_enabled = writes_enabled
        # Use default RTU framer (not ASCII) - Midnite devices use standard Modbus TCP
        # Set shorter timeout for faster failure detection
        # pymodbus default is 3 seconds, reduced to 2 for faster failure
        self._client = ModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=2,  # Read timeout per operation (reduced from default 3)
            retries=0,  # Disable retries at client level - we handle in read_holding_registers
        )
        self._lock = threading.Lock()

    def is_still_connected(self) -> bool:
        """Check if the connection is still open."""
        with self._lock:
            return self._client.is_socket_open()

    def connect(self) -> bool | None:
        """Connect to the Modbus TCP server with timeout."""
        with self._lock:
            # Ensure any existing connection is closed first
            if self._client.is_socket_open():
                _LOGGER.debug("Closing existing connection before reconnect")
                self._client.close()

            # Get socket from pymodbus client and set explicit timeout
            _LOGGER.info("Connecting to %s:%s", self.host, self.port)

            # Try to get the socket and set timeout
            try:
                # pymodbus connect() returns True on success, False on failure
                result = self._client.connect()

                # Set a very short timeout for socket operations if possible
                if self._client.socket:
                    try:
                        # Set socket-level timeout for read/write operations
                        self._client.socket.settimeout(3)  # 3 second socket timeout
                    except AttributeError:
                        _LOGGER.debug("Could not set socket timeout")
            except (AttributeError, TypeError):
                # Handle cases where pymodbus client doesn't have expected attributes
                _LOGGER.debug("Error during connect - pymodbus attribute issue")
                return False

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

    @property
    def writes_enabled(self) -> bool:
        """Return if writes are enabled."""
        return self._writes_enabled

    def write_register(self, address: int, value: int) -> Any | None:
        """Write a register."""
        if not self._writes_enabled:
            _LOGGER.warning(
                "Write attempt to register %s blocked by write protection", address
            )
            return None

        # Midnite devices use unit_id 1 by default
        with self._lock:
            return self._client.write_register(
                address=address - 1,  # Modbus addresses are 0-indexed
                value=value,
                # device_id=1,  # Removed - may cause issues with certain registers
            )

    def read_holding_registers(self, address: int, count: int = 1) -> Any | None:
        """Read holding registers with enhanced retry logic and debug logging.

        Uses a shorter timeout to fail faster when device is offline.
        """
        _LOGGER.debug("Reading register %s (count=%s)", address, count)
        # Midnite devices use unit_id 1 by default

        max_retries = 2
        with self._lock:
            for attempt in range(max_retries):
                try:
                    # Ensure connection is active before reading
                    if not self._client.is_socket_open():
                        _LOGGER.debug(
                            "Connection closed, reconnecting before read attempt %s",
                            attempt + 1,
                        )
                        success = self.connect()
                        if not success:
                            _LOGGER.warning(
                                "Reconnect failed on attempt %s", attempt + 1
                            )
                            continue

                        # Add a small delay after connect to allow device to stabilize
                        time.sleep(0.3)

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

                    # If we get here, the result has an error
                    _LOGGER.warning(
                        "Attempt %s failed for address %s: %s",
                        attempt + 1,
                        address,
                        result,
                    )

                except OSError as e:
                    error_msg = str(e)
                    _LOGGER.debug(
                        "Attempt %s exception for address %s: %s",
                        attempt + 1,
                        address,
                        e,
                    )

                    # Special handling for connection-related errors
                    if (
                        "Connection unexpectedly closed" in error_msg
                        or "timed out" in error_msg
                    ):
                        _LOGGER.debug("Connection was lost during read, will reconnect")
                        self.disconnect()
                    elif (
                        "Unable to decode request" in error_msg
                        or "byte_count" in error_msg
                    ):
                        _LOGGER.debug(
                            "Modbus protocol issue detected with this register range"
                        )
                        # Try to reset connection on protocol errors
                        if attempt < max_retries - 1:
                            self.disconnect()

                except (ModbusException, ConnectionException) as e:
                    _LOGGER.warning(
                        "Unexpected error reading address %s (attempt %s): %s",
                        address,
                        attempt + 1,
                        e,
                    )
                    # Don't retry on connection exceptions - fail immediately
                    break

                # Retry logic with backoff
                if attempt < max_retries - 1:
                    backoff_time = 0.2 * (attempt + 1)
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
