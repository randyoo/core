"""Core entity definition classes for midnite_classic integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EntityDefinition:
    """Base data class representing an entity definition."""

    # Entity identification
    key: str
    name: str

    # Register mapping
    register_group: str = "0"
    register_address: int = 0
    secondary_registers: list[int] = field(default_factory=list)

    # Data transformation
    formula: str | Callable[[int, dict[int, int]], Any] | None = None
    write_formula: str | Callable[[Any], int] | None = None

    # Bit field extraction
    bit_extraction: dict[str, Any] | None = None

    # String extraction
    string_format: dict[str, Any] | None = None

    # Entity attributes (sensor-specific)
    device_class: str | None = None
    state_class: str | None = None
    unit: str | None = None
    precision: int | None = None

    # Entity behavior
    enabled_by_default: bool = True
    hidden: bool = False
    entity_category: str | None = None

    # Validation
    min_value: float | None = None
    max_value: float | None = None

    # Advanced features
    extra_attributes: list[str] = field(default_factory=list)

    # Options (for select entities)
    options: list[Any] | None = None

    # Mode (for number entities)
    mode: str | None = None

    # Polling interval override
    polling_interval: int | None = None

    # Icon override
    icon: str | None = None


@dataclass
class SensorDefinition(EntityDefinition):
    """Sensor-specific entity definition."""

    entity_type: str = "sensor"


@dataclass
class ButtonDefinition(EntityDefinition):
    """Button-specific entity definition."""

    entity_type: str = "button"
    press_action: str | None = None


@dataclass
class NumberDefinition(EntityDefinition):
    """Number-specific entity definition."""

    entity_type: str = "number"
    mode: str = "box"
    step: float | None = None
    min_value: float = 0.0
    max_value: float = 100.0


@dataclass
class SelectDefinition(EntityDefinition):
    """Select-specific entity definition."""

    entity_type: str = "select"


@dataclass
class TextDefinition(EntityDefinition):
    """Text-specific entity definition."""

    entity_type: str = "text"
    max_length: int | None = None
