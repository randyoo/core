"""Sensor definitions package for midnite_classic integration."""

from .basic_status import BASIC_STATUS_SENSORS
from .current_voltage import CURRENT_VOLTAGE_SENSORS
from .device_info import DEVICE_INFO_SENSORS
from .diagnostics import DIAGNOSTIC_SENSORS
from .energy import ENERGY_SENSORS
from .network import NETWORK_SENSORS
from .settings import SETTINGS_SENSORS
from .status import STATUS_SENSORS
from .temperatures import TEMPERATURE_SENSORS
from .time_settings import TIME_SETTINGS_SENSORS

# Combine all sensor definitions
SENSOR_DEFINITIONS = (
    BASIC_STATUS_SENSORS
    + CURRENT_VOLTAGE_SENSORS
    + DEVICE_INFO_SENSORS
    + DIAGNOSTIC_SENSORS
    + ENERGY_SENSORS
    + NETWORK_SENSORS
    + SETTINGS_SENSORS
    + STATUS_SENSORS
    + TEMPERATURE_SENSORS
    + TIME_SETTINGS_SENSORS
)

__all__ = [
    "SENSOR_DEFINITIONS",
]
