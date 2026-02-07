"""Support for Midnite Classic select platform."""

from __future__ import annotations

import inspect
import logging
from typing import Any, cast

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MidniteClassicCoordinator
from .select_definitions import SELECT_DEFINITIONS

_LOGGER = logging.getLogger(__name__)


def _normalize_formula_indentation(formula_str: str) -> str:
    """Normalize indentation in formula strings to handle copy-pasted code."""
    lines = formula_str.split("\n")
    if not lines:
        return formula_str

    # Find the minimum indentation (leading whitespace)
    min_indent = None
    for line in lines:
        stripped = line.lstrip()
        if stripped:  # Only consider non-empty lines
            indent = len(line) - len(stripped)
            if min_indent is None or indent < min_indent:
                min_indent = indent

    # Remove the minimum indentation from all lines
    if min_indent is not None and min_indent > 0:
        normalized_lines = []
        for line in lines:
            if len(line) >= min_indent and line[:min_indent].isspace():
                normalized_lines.append(line[min_indent:])
            else:
                normalized_lines.append(line)
        formula_str = "\n".join(normalized_lines)

    # Replace 'return' statements with assignment to value variable
    # This is needed because exec() doesn't support return statements
    return formula_str.replace("return ", "value = ")


def _create_formula_function(
    formula_str: str,
    arg_count: int,
    extra_locals: dict[str, Any] | None = None,
    second_param_name: str = "x",
) -> Any:
    """Convert a formula string to a callable function."""
    if not formula_str or callable(formula_str):
        return formula_str

    # Normalize and strip whitespace from formula
    formula_str = _normalize_formula_indentation(formula_str).strip()

    # Create locals dict with optional extra variables (like 'data')
    local_vars: dict[str, Any] = extra_locals or {}

    # Create the function based on number of arguments
    if arg_count == 2:
        # For formulas that take (value, second) - where value is computed value
        # The formula body needs to be indented with 4 spaces inside the function
        func_lines = ["    " + line for line in formula_str.split("\n")]
        formula_str = "\n".join(func_lines)

        func_str = f"""
def formula_func(value, {second_param_name}):
{formula_str}
    return value
"""
    elif arg_count == 1:
        # For formulas that take (x) - like write_formula
        func_lines = []
        for line in formula_str.split("\n"):
            stripped = line.lstrip()
            if stripped:
                func_lines.append("    " + stripped)
            else:
                func_lines.append(line)
        formula_str = "\n".join(func_lines)

        func_str = f"""
def formula_func(x):
{formula_str}
    return value
"""
    else:
        # For formulas with variable arguments
        func_lines = []
        for line in formula_str.split("\n"):
            stripped = line.lstrip()
            if stripped:
                func_lines.append("    " + stripped)
            else:
                func_lines.append(line)
        formula_str = "\n".join(func_lines)

        func_str = f"""
def formula_func(*args):
{formula_str}
    return value
"""

    # Create globals dict with proper module context for imports
    globals_dict = {
        "__name__": __name__,
        "__file__": __file__,
        "__package__": __name__.rpartition(".")[0],
    }

    try:
        exec(  # noqa: S102
            compile(func_str, "<string>", "exec"), globals_dict, local_vars
        )
        return local_vars.get("formula_func")
    except Exception as exc:  # noqa: BLE001
        _LOGGER.error("Error creating formula function: %s", exc)
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Midnite Classic selects."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Convert string formulas to lambda functions for each definition
    modified_definitions = []
    for definition in SELECT_DEFINITIONS:
        # Create a copy of the definition
        formula = None
        if callable(definition.formula):
            formula = definition.formula
        elif isinstance(definition.formula, str):
            # Read formulas use 'data' for second parameter (the register data dict)
            formula = _create_formula_function(
                definition.formula, 2, second_param_name="data"
            )

        write_formula = None
        if callable(definition.write_formula):
            write_formula = definition.write_formula
        elif isinstance(definition.write_formula, str):
            # Write formulas use 'option' for second parameter (the option string)
            write_formula = _create_formula_function(
                definition.write_formula, 2, second_param_name="option"
            )

        modified_def = type(definition)(
            key=definition.key,
            name=definition.name,
            register_group=definition.register_group,
            register_address=definition.register_address,
            secondary_registers=list(definition.secondary_registers),
            formula=formula,
            write_formula=write_formula,
            bit_extraction=definition.bit_extraction,
            string_format=definition.string_format,
            device_class=definition.device_class,
            state_class=definition.state_class,
            unit=definition.unit,
            precision=definition.precision,
            enabled_by_default=definition.enabled_by_default,
            hidden=definition.hidden,
            entity_category=definition.entity_category,
            min_value=definition.min_value,
            max_value=definition.max_value,
            extra_attributes=list(definition.extra_attributes),
            options=list(definition.options) if definition.options else None,
            mode=definition.mode,
            polling_interval=definition.polling_interval,
            icon=definition.icon,
        )
        modified_definitions.append(modified_def)

    selects = []
    for definition in modified_definitions:
        select_class = create_select_class(definition)
        selects.append(select_class(coordinator, entry))

    async_add_entities(selects)


def _execute_write_formula(
    coordinator: MidniteClassicCoordinator,
    definition: Any,
    option: str,
    current_value: int,
) -> int | None:
    """Execute the write formula and return the computed register value.

    Returns None if there's an error or non-numeric result.
    """
    uses_single_arg = False
    if callable(definition.write_formula):
        try:
            sig = inspect.signature(definition.write_formula)
            if len(sig.parameters) == 1:
                uses_single_arg = True
        except Exception:  # noqa: BLE001
            pass

    try:
        if uses_single_arg:
            register_value = definition.write_formula(option)
        else:
            register_value = definition.write_formula(current_value, option)

        if isinstance(register_value, (int, float)):
            return int(register_value)
    except Exception:  # noqa: BLE001
        _LOGGER.debug(
            "Error in write formula for select %s",
            definition.name,
        )
    return None


def _determine_write_register(definition: Any, combined_value: int) -> tuple[int, int]:
    """Determine register address and value to write.

    Returns (register_address, register_value_int).
    """
    combined_value = combined_value & 0xFFFFFFFF
    low_value = combined_value & 0xFFFF
    high_value = (combined_value >> 16) & 0xFFFF

    if definition.secondary_registers and high_value > 0:
        return (definition.secondary_registers[0], high_value)
    return (definition.register_address, low_value)


def create_select_class(definition: Any):
    """Dynamically create a select class for the given definition."""

    class DynamicSelect(CoordinatorEntity[MidniteClassicCoordinator], SelectEntity):
        """Dynamic select based on definition."""

        def __init__(
            self, coordinator: MidniteClassicCoordinator, entry: ConfigEntry
        ) -> None:
            """Initialize the select."""
            super().__init__(coordinator)
            self._entry = entry
            self._definition = definition

            # Set basic attributes from definition
            self._attr_name = definition.name
            self._attr_unique_id = f"{entry.entry_id}_{definition.key}"
            if hasattr(definition, "icon"):
                self._attr_icon = definition.icon
            if hasattr(definition, "entity_category"):
                self._attr_entity_category = definition.entity_category

        @property
        def device_info(self) -> DeviceInfo | None:
            """Return device info."""
            # Get device info from coordinator (includes MAC address from modbus)
            return self.coordinator.update_device_info()

        @property
        def current_option(self) -> str | None:
            """Return the selected option."""
            # Evaluate formula to get current value
            if callable(self._definition.formula):
                try:
                    # Get register data from coordinator
                    group_data = self.coordinator.data.get("data", {}).get(
                        self._definition.register_group, {}
                    )
                    current_value = group_data.get(self._definition.register_address, 0)

                    # Call formula with (value, data_dict) - pass group_data as second argument
                    current_value = self._definition.formula(current_value, group_data)
                    return cast(str | None, current_value)
                except Exception as exc:  # noqa: BLE001
                    _LOGGER.error(
                        "Error evaluating formula for select %s: %s",
                        self._attr_name,
                        exc,
                    )
                    # For write-only registers, return None as current option
                    # The user will select an option to change the state
                    return None
            else:
                # Fallback - shouldn't happen with proper definitions
                return None

        @property
        def options(self) -> list[str]:
            """Return the available options."""
            if hasattr(self._definition, "options") and self._definition.options:
                options_list = cast(list[str | None], self._definition.options)
                # Filter out None values for options list (Home Assistant requires str only)
                return [opt for opt in options_list if opt is not None]
            return []

        async def _read_register_value(self, register_address: int) -> int | None:
            """Read a register value with error handling."""
            try:
                current_register_value = await self.hass.async_add_executor_job(
                    self.coordinator.api.read_holding_registers,
                    int(register_address),
                    1,
                )
                if not current_register_value:
                    _LOGGER.error(
                        "Failed to read current value from register %s",
                        register_address,
                    )
                    return None
                return current_register_value[0]
            except Exception as exc:  # noqa: BLE001
                _LOGGER.error(
                    "Failed to read register %s: %s",
                    register_address,
                    exc,
                )
                return None

        async def async_select_option(self, option: str) -> None:
            """Change the selected option."""
            register_address = self._definition.register_address

            # Determine if we should skip reading (write-only registers)
            skip_read = register_address in (4160, 4161)

            # Read current value unless skip_read is True
            current_value = 0
            if not skip_read:
                read_result = await self._read_register_value(register_address)
                if read_result is not None:
                    current_value = read_result

            # Compute the register value using write formula
            register_value = _execute_write_formula(
                self.coordinator, self._definition, option, current_value
            )
            if register_value is None:
                return

            # Determine which register to write to and the value
            register_address, register_value_int = _determine_write_register(
                self._definition, register_value
            )

            # Check if writes are enabled before proceeding
            if not self.coordinator.api.writes_enabled:
                _LOGGER.info(
                    "Write protection enabled - select %s would write %s to register %s",
                    self._definition.name,
                    register_value_int,
                    register_address,
                )
                return

            # Write to register
            try:
                await self.hass.async_add_executor_job(
                    self.coordinator.api.write_register,
                    int(register_address),
                    register_value_int,
                )

                _LOGGER.info(
                    "Select %s wrote %s to register %s",
                    self._definition.name,
                    register_value_int,
                    register_address,
                )

                # Force a refresh to show the updated value
                await self.coordinator.async_refresh()
            except (ValueError, TypeError) as exc:
                _LOGGER.error(
                    "Failed to write select %s to register %s: %s",
                    self._definition.key,
                    register_address,
                    exc,
                )

    return DynamicSelect
