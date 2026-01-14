"""Tests for midnite_classic entity factory."""

from __future__ import annotations

import pytest

from homeassistant.components.midnite_classic.const import DOMAIN
from homeassistant.components.midnite_classic.entity_factory import evaluate_formula

from tests.common import MockConfigEntry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Midnight Solar Classic",
        domain=DOMAIN,
        data={
            "host": "127.0.0.1",
            "port": 502,
            "device_id": "test_device",
            "mac_address": "AA:BB:CC:DD:EE:FF",
        },
    )


@pytest.mark.parametrize(
    "formula,registers,data,expected",
    [
        # Simple register value
        ("R1", {1: 250}, None, 250),
        # Register with scaling
        ("R1 * 0.1", {1: 250}, None, 25.0),
        # Multiple registers
        ("(R1 + R2) / 2", {1: 240, 2: 260}, None, 250.0),
        # Register with offset
        ("R1 - 1000", {1: 1500}, None, 500),
        # Complex formula
        ("(R1 * R2) / 1000", {1: 100, 2: 200}, None, 20.0),
    ],
)
def test_evaluate_formula(
    formula: str, registers: dict[int, int], data: dict | None, expected: float
) -> None:
    """Test formula evaluation."""
    result = evaluate_formula(formula, registers, data or {})
    assert result == expected


@pytest.mark.parametrize(
    "formula,registers,data",
    [
        # Missing register
        ("R1", {}, {}),
        # Invalid formula syntax
        ("R1 +", {1: 100}, {}),
        # Division by zero
        ("R1 / R2", {1: 100, 2: 0}, {}),
    ],
)
def test_evaluate_formula_errors(
    formula: str, registers: dict[int, int], data: dict
) -> None:
    """Test formula evaluation errors."""
    with pytest.raises(ValueError):
        evaluate_formula(formula, registers, data)
