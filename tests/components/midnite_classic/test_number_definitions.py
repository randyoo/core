"""Tests for midnite_classic number entity definitions."""

import pytest

from homeassistant.components.midnite_classic.entity_definitions import NumberDefinition
from homeassistant.components.midnite_classic.number_definitions import (
    NUMBER_DEFINITIONS,
)


@pytest.fixture
def number_definitions():
    """Return the number definitions."""
    return NUMBER_DEFINITIONS


def test_number_definitions_count(number_definitions):
    """Test that we have the expected number of number definitions."""
    assert len(number_definitions) == 10


def test_number_definitions_types(number_definitions):
    """Test that all definitions are NumberDefinition instances."""
    for definition in number_definitions:
        assert isinstance(definition, NumberDefinition)


def test_absorb_voltage_definition():
    """Test absorb voltage number definition."""
    definition = next(d for d in NUMBER_DEFINITIONS if d.key == "absorb_voltage")
    assert definition.name == "Absorb Voltage"
    assert definition.register_group == "settings"
    assert definition.register_address == 4150
    assert definition.min_value == 40.0
    assert definition.max_value == 65.0
    assert definition.step == 0.1
    assert definition.device_class == "voltage"
    assert definition.unit == "V"


def test_float_voltage_definition():
    """Test float voltage number definition."""
    definition = next(d for d in NUMBER_DEFINITIONS if d.key == "float_voltage")
    assert definition.name == "Float Voltage"
    assert definition.register_group == "settings"
    assert definition.register_address == 4151
    assert definition.min_value == 40.0
    assert definition.max_value == 65.0


def test_equalize_voltage_definition():
    """Test equalize voltage number definition."""
    definition = next(d for d in NUMBER_DEFINITIONS if d.key == "equalize_voltage")
    assert definition.name == "Equalize Voltage"
    assert definition.register_group == "settings"
    assert definition.register_address == 4152
    assert definition.min_value == 40.0
    assert definition.max_value == 65.0


def test_absorb_current_limit_definition():
    """Test absorb current limit number definition."""
    definition = next(d for d in NUMBER_DEFINITIONS if d.key == "absorb_current_limit")
    assert definition.name == "Absorb Current Limit"
    assert definition.register_group == "settings"
    assert definition.register_address == 4153
    assert definition.min_value == 0.0
    assert definition.max_value == 200.0
    assert definition.step == 1.0
    assert definition.device_class == "current"
    assert definition.unit == "A"


def test_float_current_limit_definition():
    """Test float current limit number definition."""
    definition = next(d for d in NUMBER_DEFINITIONS if d.key == "float_current_limit")
    assert definition.name == "Float Current Limit"
    assert definition.register_group == "settings"
    assert definition.register_address == 4154
    assert definition.min_value == 0.0
    assert definition.max_value == 200.0


def test_absorb_time_definition():
    """Test absorb time number definition."""
    definition = next(d for d in NUMBER_DEFINITIONS if d.key == "absorb_time")
    assert definition.name == "Absorb Time"
    assert definition.register_group == "time_settings"
    assert definition.register_address == 4139
    assert definition.min_value == 0.0
    assert definition.max_value == 720.0
    assert definition.device_class == "duration"
    assert definition.unit == "minutes"


def test_equalize_time_definition():
    """Test equalize time number definition."""
    definition = next(d for d in NUMBER_DEFINITIONS if d.key == "equalize_time")
    assert definition.name == "Equalize Time"
    assert definition.register_group == "time_settings"
    assert definition.register_address == 4143
    assert definition.min_value == 0.0
    assert definition.max_value == 720.0


def test_equalize_days_definition():
    """Test equalize days number definition."""
    definition = next(d for d in NUMBER_DEFINITIONS if d.key == "equalize_days")
    assert definition.name == "Equalize Days"
    assert definition.register_group == "time_settings"
    assert definition.register_address == 4145
    assert definition.min_value == 0
    assert definition.max_value == 365


def test_temp_compensation_definition():
    """Test temperature compensation number definition."""
    definition = next(d for d in NUMBER_DEFINITIONS if d.key == "temp_compensation")
    assert definition.name == "Temperature Compensation"
    assert definition.register_group == "settings"
    assert definition.register_address == 4155
    assert definition.min_value == -20.0
    assert definition.max_value == 20.0
    assert definition.device_class == "temperature"
    assert definition.unit == "%/°C"


def test_modbus_timeout_definition():
    """Test modbus timeout number definition."""
    definition = next(d for d in NUMBER_DEFINITIONS if d.key == "modbus_timeout")
    assert definition.name == "Modbus Timeout"
    assert definition.register_group == "network"
    assert definition.register_address == 20496
    assert definition.min_value == 0.5
    assert definition.max_value == 30.0
    assert definition.step == 0.5
    assert definition.device_class == "duration"
    assert definition.unit == "seconds"


def test_all_numbers_have_write_formulas(number_definitions):
    """Test that all number definitions have write formulas."""
    for definition in number_definitions:
        assert definition.write_formula is not None, (
            f"Number definition {definition.key} is missing write_formula"
        )
