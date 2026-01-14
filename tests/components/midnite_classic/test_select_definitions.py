"""Tests for midnite_classic select entity definitions."""

import pytest

from homeassistant.components.midnite_classic.entity_definitions import SelectDefinition
from homeassistant.components.midnite_classic.select_definitions import (
    SELECT_DEFINITIONS,
)


@pytest.fixture
def select_definitions():
    """Return the select definitions."""
    return SELECT_DEFINITIONS


def test_select_definitions_count(select_definitions):
    """Test that we have the expected number of select definitions."""
    assert len(select_definitions) == 3


def test_select_definitions_types(select_definitions):
    """Test that all definitions are SelectDefinition instances."""
    for definition in select_definitions:
        assert isinstance(definition, SelectDefinition)


def test_charge_mode_definition():
    """Test charge mode select definition."""
    definition = next(d for d in SELECT_DEFINITIONS if d.key == "charge_mode")
    assert definition.name == "Charge Mode"
    assert definition.register_group == "settings"
    assert definition.register_address == 4162
    assert definition.options == [
        "Standard",
        "PV Only",
        "Battery Only",
        "Manual",
    ]


def test_device_type_override_definition():
    """Test device type override select definition."""
    definition = next(d for d in SELECT_DEFINITIONS if d.key == "device_type_override")
    assert definition.name == "Device Type Override"
    assert definition.register_group == "settings"
    assert definition.register_address == 4101
    assert definition.options == [
        "Classic CC",
        "Classic LS",
        "Classic HV",
        "Classic LV",
    ]


def test_communication_mode_definition():
    """Test communication mode select definition."""
    definition = next(d for d in SELECT_DEFINITIONS if d.key == "communication_mode")
    assert definition.name == "Communication Mode"
    assert definition.register_group == "settings"
    assert definition.register_address == 4163
    assert definition.options == [
        "Modbus RTU",
        "Modbus TCP",
        "MidNite Network",
    ]


def test_all_selects_have_write_formulas(select_definitions):
    """Test that all select definitions have write formulas."""
    for definition in select_definitions:
        assert definition.write_formula is not None, (
            f"Select definition {definition.key} is missing write_formula"
        )
