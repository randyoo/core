"""Support for Midnite Solar devices."""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from pymodbus.client import ModbusTcpClient
else:
    ModbusTcpClient = None

_LOGGER = logging.getLogger(__name__)


class MidniteClassicHub:
    """Midnite Classic Hub for managing Modbus TCP connections."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize the hub."""
        self.host = host
        self.port = port
        if ModbusTcpClient is not None:
            self._client = cast(Any, ModbusTcpClient(host=self.host, port=self.port))
        else:
            self._client = None
        self._lock = threading.Lock()

    def is_still_connected(self) -> bool:
        """Check if the connection is still open."""
        if self._client is None:
            return False
        with self._lock:
            return cast(Any, self._client).is_socket_open()

    def connect(self) -> bool | None:
        """Connect to the Modbus TCP server."""
        if self._client is None:
            _LOGGER.error("Pymodbus not available")
            return False
        with self._lock:
            _LOGGER.debug("Connecting to %s:%s", self.host, self.port)
            result = cast(Any, self._client).connect()
            _LOGGER.debug("Connection result: %s", result)
            return result

    def disconnect(self) -> bool | None:
        """Disconnect from the Modbus TCP server."""
        if self._client is None:
            return False
        with self._lock:
            client = cast(Any, self._client)
            if client.is_socket_open():
                _LOGGER.debug("Disconnecting from %s:%s", self.host, self.port)
                return client.close()
            return None

    def write_register(self, address: int, value: int) -> bool | None:
        """Write a register."""
        if self._client is None:
            _LOGGER.error("Pymodbus not available")
            return False
        # Midnite devices use unit_id 1 by default
        with self._lock:
            try:
                result = cast(Any, self._client).write_register(
                    address=address - 1,  # Modbus addresses are 0-indexed
                    value=value,
                    # device_id=1,  # Removed - may cause issues with certain registers
                )
                return result.isError() is False
            except OSError as exc:
                _LOGGER.error("Failed to write register %s: %s", address, exc)
                raise

    def read_holding_registers(self, address: int, count: int = 1) -> Any | None:
        """Read holding registers with enhanced retry logic and debug logging."""
        if self._client is None:
            _LOGGER.error("Pymodbus not available")
            return None

        # Detailed connection state logging
        socket_open = cast(Any, self._client).is_socket_open()
        _LOGGER.debug(
            "Reading unit 1 address %s count %s. Socket open: %s",
            address,
            count,
            socket_open,
        )
        # Midnite devices use unit_id 1 by default

        max_retries = 5  # Increased from 3 to 5 for better reliability
        with self._lock:
            for attempt in range(max_retries):
                try:
                    client = cast(Any, self._client)
                    # Ensure connection is active before reading
                    if not client.is_socket_open():
                        _LOGGER.debug(
                            "Connection closed, reconnecting before read attempt %s",
                            attempt + 1,
                        )
                        connect_result = self.connect()
                        _LOGGER.debug("Connect result: %s", connect_result)
                        # Add a small delay after connect to allow device to stabilize
                        time.sleep(0.2)

                    # Log detailed request information
                    modbus_address = address - 1  # Modbus addresses are 0-indexed
                    _LOGGER.debug(
                        "Sending Modbus request: address=%s (raw=%s), count=%s, unit=1",
                        address,
                        modbus_address,
                        count,
                    )

                    result = client.read_holding_registers(
                        address=modbus_address,
                        count=count,
                        # device_id=1,  # Removed - may cause issues with certain registers like 20492/20493
                    )

                    if result is not None and not result.isError():
                        _LOGGER.debug(
                            "Successfully read address %s: %s (raw=%s)",
                            address,
                            result.registers,
                            modbus_address,
                        )
                        return result

                    # Log detailed error information
                    error_details = {
                        "function_code": getattr(result, "function_code", "N/A"),
                        "exception_code": getattr(result, "exception_code", "N/A"),
                        "isError": result.isError() if result else "N/A",
                    }
                    _LOGGER.warning(
                        "Attempt %s failed for address %s: %s. Details: %s",
                        attempt + 1,
                        address,
                        result,
                        error_details,
                    )

                except OSError as exc:
                    # Special handling for "Unable to decode request" errors
                    error_msg = str(exc)
                    _LOGGER.debug("Full exception details: %s", exc, exc_info=True)
                    if (
                        "Unable to decode request" in error_msg
                        or "byte_count" in error_msg
                    ):
                        _LOGGER.warning(
                            "Attempt %s exception for address %s: %s",
                            attempt + 1,
                            address,
                            exc,
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
                        _LOGGER.warning(
                            "Attempt %s exception for address %s: %s",
                            attempt + 1,
                            address,
                            exc,
                        )

                    if attempt < max_retries - 1:
                        backoff_time = 0.2 * (
                            attempt + 1
                        )  # Increased exponential backoff
                        _LOGGER.debug(
                            "Waiting %ss before retry %s", backoff_time, attempt + 2
                        )
                        time.sleep(backoff_time)

            _LOGGER.error(
                "All %s attempts failed for address %s, count=%s",
                max_retries,
                address,
                count,
            )
            return None
