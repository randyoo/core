"""Tests for midnite_classic text entity definitions."""

import pytest

from homeassistant.components.midnite_classic.entity_definitions import TextDefinition
from homeassistant.components.midnite_classic.text_definitions import TEXT_DEFINITIONS


@pytest.fixture
def text_definitions():
    """Return the text definitions."""
    return TEXT_DEFINITIONS


def test_text_definitions_count(text_definitions):
    """Test that we have the expected number of text definitions."""
    assert len(text_definitions) == 1


def test_text_definitions_types(text_definitions):
    """Test that all definitions are TextDefinition instances."""
    for definition in text_definitions:
        assert isinstance(definition, TextDefinition)


def test_device_name_definition():
    """Test device name text definition."""
    definition = next(d for d in TEXT_DEFINITIONS if d.key == "device_name")
    assert definition.name == "Device Name"
    assert definition.register_group == "settings"
    assert definition.register_address == 4170
    assert definition.secondary_registers == [4171, 4172]
    assert definition.max_length == 24


def test_all_texts_have_write_formulas(text_definitions):
    """Test that all text definitions have write formulas."""
    for definition in text_definitions:
        assert definition.write_formula is not None, (
            f"Text definition {definition.key} is missing write_formula"
        )
