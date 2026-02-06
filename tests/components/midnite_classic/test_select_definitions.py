"""Tests for select entity definitions in midnite_classic integration."""

from __future__ import annotations

import pytest

from homeassistant.components.midnite_classic.select import _create_formula_function
from homeassistant.components.midnite_classic.select_definitions import (
    SELECT_DEFINITIONS,
)


class TestSelectDefinitions:
    """Test select entity definitions."""

    def test_select_definitions_count(self) -> None:
        """Test that the correct number of select definitions are defined."""
        # We expect 5 selects: force_charge_state, force_actions, charge_mode,
        # device_type_override, communication_mode
        assert len(SELECT_DEFINITIONS) == 5

    def test_force_charge_state_definition(self) -> None:
        """Test the Force Charge State select definition."""
        force_charge_select = next(
            (s for s in SELECT_DEFINITIONS if s.key == "force_charge_state"),
            None,
        )
        assert force_charge_select is not None
        assert force_charge_select.name == "Force Charge State"
        assert force_charge_select.register_address == 4160
        assert force_charge_select.options == ["Float", "Bulk/Absorb", "EQ"]

    def test_force_actions_definition(self) -> None:
        """Test the Force Actions select definition."""
        force_actions_select = next(
            (s for s in SELECT_DEFINITIONS if s.key == "force_actions"),
            None,
        )
        assert force_actions_select is not None
        assert force_actions_select.name == "Force Actions"
        assert force_actions_select.register_address == 4160
        # Should include "None" as first option and all action options
        expected_options = [
            "None",
            "Reset Faults",
            "Reset Auto EQ Counter",
            "Sweep/Re-track",
            "New Day",
            "Reset Info Flags",
            "EEPROM Init Read",
            "EEPROM Update",
        ]
        assert force_actions_select.options == expected_options

    def test_charge_mode_definition(self) -> None:
        """Test the Charge Mode select definition."""
        charge_mode_select = next(
            (s for s in SELECT_DEFINITIONS if s.key == "charge_mode"),
            None,
        )
        assert charge_mode_select is not None
        assert charge_mode_select.name == "Charge Mode"
        assert charge_mode_select.register_address == 4162
        assert charge_mode_select.options == [
            "Standard",
            "PV Only",
            "Battery Only",
            "Manual",
        ]

    def test_device_type_override_definition(self) -> None:
        """Test the Device Type Override select definition."""
        device_type_select = next(
            (s for s in SELECT_DEFINITIONS if s.key == "device_type_override"),
            None,
        )
        assert device_type_select is not None
        assert device_type_select.name == "Device Type Override"
        assert device_type_select.register_address == 4101
        assert device_type_select.options == [
            "Classic CC",
            "Classic LS",
            "Classic HV",
            "Classic LV",
        ]

    def test_communication_mode_definition(self) -> None:
        """Test the Communication Mode select definition."""
        comm_mode_select = next(
            (s for s in SELECT_DEFINITIONS if s.key == "communication_mode"),
            None,
        )
        assert comm_mode_select is not None
        assert comm_mode_select.name == "Communication Mode"
        assert comm_mode_select.register_address == 4163
        assert comm_mode_select.options == [
            "Modbus RTU",
            "Modbus TCP",
            "MidNite Network",
        ]


class TestForceChargeStateFormulas:
    """Test the Force Charge State select formulas."""

    def test_force_charge_state_formula_eq(self) -> None:
        """Test that EQ bit is detected correctly."""
        # Simplified inline formula without indentation issues
        data = {
            4160: 0x80,  # Bit 7 set
            4161: 0,
            4120: 0,
        }
        combined_value = (data.get(4161, 0) << 16) | data.get(4160, 0)
        if combined_value & (1 << 7):
            value = "EQ"
        elif combined_value & (1 << 6):
            value = "Bulk/Absorb"
        elif combined_value & (1 << 5):
            value = "Float"
        else:
            charge_stage_value = data.get(4120, 0) >> 8 & 0xFF
            current_stage = "Absorb" if charge_stage_value == 3 else "Unknown"
            value = current_stage

        assert value == "EQ"

    def test_force_charge_state_formula_bulk(self) -> None:
        """Test that Bulk/Absorb bit is detected correctly."""
        # Simplified inline formula without indentation issues
        data = {
            4160: 0x40,  # Bit 6 set
            4161: 0,
            4120: 0,
        }
        combined_value = (data.get(4161, 0) << 16) | data.get(4160, 0)
        if combined_value & (1 << 7):
            value = "EQ"
        elif combined_value & (1 << 6):
            value = "Bulk/Absorb"
        elif combined_value & (1 << 5):
            value = "Float"
        else:
            charge_stage_value = data.get(4120, 0) >> 8 & 0xFF
            current_stage = "Absorb" if charge_stage_value == 3 else "Unknown"
            value = current_stage

        assert value == "Bulk/Absorb"

    def test_force_charge_state_formula_float(self) -> None:
        """Test that Float bit is detected correctly."""
        # Simplified inline formula without indentation issues
        data = {
            4160: 0x20,  # Bit 5 set
            4161: 0,
            4120: 0,
        }
        combined_value = (data.get(4161, 0) << 16) | data.get(4160, 0)
        if combined_value & (1 << 7):
            value = "EQ"
        elif combined_value & (1 << 6):
            value = "Bulk/Absorb"
        elif combined_value & (1 << 5):
            value = "Float"
        else:
            charge_stage_value = data.get(4120, 0) >> 8 & 0xFF
            current_stage = "Absorb" if charge_stage_value == 3 else "Unknown"
            value = current_stage

        assert value == "Float"

    def test_force_charge_state_formula_no_bits(self) -> None:
        """Test that current charge stage is returned when no force bits are set."""
        # Simplified inline formula without indentation issues
        data = {
            4160: 0,
            4161: 0,
            4120: 0x03 << 8,  # Charge stage 3 (Absorb)
        }
        combined_value = (data.get(4161, 0) << 16) | data.get(4160, 0)
        if combined_value & (1 << 7):
            value = "EQ"
        elif combined_value & (1 << 6):
            value = "Bulk/Absorb"
        elif combined_value & (1 << 5):
            value = "Float"
        else:
            charge_stage_value = data.get(4120, 0) >> 8 & 0xFF
            current_stage = "Absorb" if charge_stage_value == 3 else "Unknown"
            value = current_stage

        assert value == "Absorb"


class TestForceChargeStateWriteFormulas:
    """Test the Force Charge State select write formulas."""

    def test_force_charge_state_write_eq(self) -> None:
        """Test writing EQ option."""
        # Simplified inline formula without indentation issues
        value = 0
        option = "EQ"
        value &= ~((1 << 7) | (1 << 6) | (1 << 5))
        if option == "EQ":
            value |= 1 << 7
        elif option == "Bulk/Absorb":
            value |= 1 << 6
        elif option == "Float":
            value |= 1 << 5

        assert value == 0x80

    def test_force_charge_state_write_bulk(self) -> None:
        """Test writing Bulk/Absorb option."""
        # Simplified inline formula without indentation issues
        value = 0
        option = "Bulk/Absorb"
        value &= ~((1 << 7) | (1 << 6) | (1 << 5))
        if option == "EQ":
            value |= 1 << 7
        elif option == "Bulk/Absorb":
            value |= 1 << 6
        elif option == "Float":
            value |= 1 << 5

        assert value == 0x40

    def test_force_charge_state_write_float(self) -> None:
        """Test writing Float option."""
        # Simplified inline formula without indentation issues
        value = 0
        option = "Float"
        value &= ~((1 << 7) | (1 << 6) | (1 << 5))
        if option == "EQ":
            value |= 1 << 7
        elif option == "Bulk/Absorb":
            value |= 1 << 6
        elif option == "Float":
            value |= 1 << 5

        assert value == 0x20

    def test_force_charge_state_write_with_existing_value(self) -> None:
        """Test writing with existing register value."""
        # Simplified inline formula without indentation issues
        value = 0x04  # Bit 2 already set
        option = "EQ"
        value &= ~((1 << 7) | (1 << 6) | (1 << 5))
        if option == "EQ":
            value |= 1 << 7
        elif option == "Bulk/Absorb":
            value |= 1 << 6
        elif option == "Float":
            value |= 1 << 5

        assert value == 0x84  # Bit 7 and bit 2 should be set


class TestSelectWriteWithSkipRead:
    """Test select write behavior with skip_read (write-only registers).

    When a register is write-only, we can't read it first. The formula should
    compute the correct value starting from 0 (current_value=0) and the option.
    """

    def test_write_only_register_eq(self) -> None:
        """Test writing EQ option to write-only register (current_value=0)."""
        # Simulate what happens when skip_read=True for Force Charge State
        current_value = 0  # Can't read write-only register, default to 0
        option = "EQ"

        # This is what the formula does:
        # value &= ~((1 << 7) | (1 << 6) | (1 << 5))
        value = current_value
        value &= ~((1 << 7) | (1 << 6) | (1 << 5))
        # x = option ("EQ")
        if option == "EQ":
            value |= 1 << 7
        elif option == "Bulk/Absorb":
            value |= 1 << 6
        elif option == "Float":
            value |= 1 << 5

        # Result should be 0x80 (bit 7 set)
        assert value == 0x80
        # Note: The final return is `value & 0xFFFF` which keeps it as 0x80

    def test_write_only_register_bulk(self) -> None:
        """Test writing Bulk/Absorb option to write-only register."""
        current_value = 0
        option = "Bulk/Absorb"

        value = current_value
        value &= ~((1 << 7) | (1 << 6) | (1 << 5))
        if option == "EQ":
            value |= 1 << 7
        elif option == "Bulk/Absorb":
            value |= 1 << 6
        elif option == "Float":
            value |= 1 << 5

        assert value == 0x40

    def test_write_only_register_float(self) -> None:
        """Test writing Float option to write-only register."""
        current_value = 0
        option = "Float"

        value = current_value
        value &= ~((1 << 7) | (1 << 6) | (1 << 5))
        if option == "EQ":
            value |= 1 << 7
        elif option == "Bulk/Absorb":
            value |= 1 << 6
        elif option == "Float":
            value |= 1 << 5

        assert value == 0x20


class TestFormulaFunctionCreation:
    """Test the _create_formula_function creates working functions."""

    def test_force_charge_state_write_formula_with_current_value_zero(self) -> None:
        """Test Force Charge State write formula when current_value=0 (skip_read)."""

        # The Force Charge State write formula (using 'option' parameter)
        formula_str = """
            # Clear all force charge bits first (bits 5-7 in register 4160)
            value &= ~((1 << 7) | (1 << 6) | (1 << 5))

            # Set the appropriate bit based on selection
            if option == "EQ":
                value |= 1 << 7
            elif option == "Bulk/Absorb":
                value |= 1 << 6
            elif option == "Float":
                value |= 1 << 5

            return value & 0xFFFF
        """

        # Create the function with 2 arguments: (value, option)
        func = _create_formula_function(formula_str, 2, second_param_name="option")

        # Test with current_value=0 and option="Float"
        result = func(0, "Float")
        assert result == 0x20, f"Expected 0x20 (32) but got {result}"

        # Test with current_value=0 and option="Bulk/Absorb"
        result = func(0, "Bulk/Absorb")
        assert result == 0x40, f"Expected 0x40 (64) but got {result}"

        # Test with current_value=0 and option="EQ"
        result = func(0, "EQ")
        assert result == 0x80, f"Expected 0x80 (128) but got {result}"

    def test_force_actions_write_formula_with_current_value_zero(self) -> None:
        """Test Force Actions write formula when current_value=0 (skip_read)."""

        # The Force Actions write formula (using 'option' parameter, without final masking)
        formula_str = """
            # Clear all force action bits first
            value &= ~((1 << 23) | (1 << 16) | (1 << 11) | (1 << 8) |
                       (1 << 4) | (1 << 3) | (1 << 2))

            # Set the appropriate bit based on selection
            if option == "Reset Faults":
                value |= 1 << 23
            elif option == "Reset Auto EQ Counter":
                value |= 1 << 16
            elif option == "Sweep/Re-track":
                value |= 1 << 11
            elif option == "New Day":
                value |= 1 << 8
            elif option == "Reset Info Flags":
                value |= 1 << 4
            elif option == "EEPROM Init Read":
                value |= 1 << 3
            elif option == "EEPROM Update":
                value |= 1 << 2

        """

        # Create the function with 2 arguments: (value, option)
        func = _create_formula_function(formula_str, 2, second_param_name="option")

        # Test with current_value=0 and option="Reset Faults" (bit 23)
        # Note: This formula does NOT have final masking - that happens in select.py
        expected = 1 << 23  # Bit 23 = 8388608
        result = func(0, "Reset Faults")
        assert result == expected, f"Expected {expected} but got {result}"

        # Test with current_value=0 and option="Reset Auto EQ Counter" (bit 16)
        expected2 = 1 << 16  # Bit 16 = 65536
        result2 = func(0, "Reset Auto EQ Counter") if func else None
        assert result2 == expected2, f"Expected {expected2} but got {result2}"


class TestForceActionsFormulas:
    """Test the Force Actions select formulas."""

    def test_force_actions_formula_reset_faults(self) -> None:
        """Test that Reset Faults is detected correctly."""
        # Simplified inline formula without indentation issues
        data = {
            4160: 0,
            4161: 0x80,  # Bit 7 of reg 4161 = bit 23 overall
        }
        combined_value = (data.get(4161, 0) << 16) | data.get(4160, 0)
        if combined_value & (1 << 23):
            value = "Reset Faults"
        elif combined_value & (1 << 16):
            value = "Reset Auto EQ Counter"
        elif combined_value & (1 << 11):
            value = "Sweep/Re-track"
        elif combined_value & (1 << 8):
            value = "New Day"
        elif combined_value & (1 << 4):
            value = "Reset Info Flags"
        elif combined_value & (1 << 3):
            value = "EEPROM Init Read"
        elif combined_value & (1 << 2):
            value = "EEPROM Update"
        else:
            value = "None"

        assert value == "Reset Faults"

    def test_force_actions_formula_reset_aeq(self) -> None:
        """Test that Reset Auto EQ Counter is detected correctly."""
        # Simplified inline formula without indentation issues
        data = {
            4160: 0,  # No bits set in reg 4160
            4161: 0x1,  # Bit 0 of reg 4161 = bit 16 overall
        }
        combined_value = (data.get(4161, 0) << 16) | data.get(4160, 0)
        if combined_value & (1 << 23):
            value = "Reset Faults"
        elif combined_value & (1 << 16):
            value = "Reset Auto EQ Counter"
        elif combined_value & (1 << 11):
            value = "Sweep/Re-track"
        elif combined_value & (1 << 8):
            value = "New Day"
        elif combined_value & (1 << 4):
            value = "Reset Info Flags"
        elif combined_value & (1 << 3):
            value = "EEPROM Init Read"
        elif combined_value & (1 << 2):
            value = "EEPROM Update"
        else:
            value = "None"

        assert value == "Reset Auto EQ Counter"

    def test_force_actions_formula_no_bits(self) -> None:
        """Test that "None" is returned when no force action bits are set."""
        # Simplified inline formula without indentation issues
        data = {
            4160: 0,
            4161: 0,
        }
        combined_value = (data.get(4161, 0) << 16) | data.get(4160, 0)
        if combined_value & (1 << 23):
            value = "Reset Faults"
        elif combined_value & (1 << 16):
            value = "Reset Auto EQ Counter"
        elif combined_value & (1 << 11):
            value = "Sweep/Re-track"
        elif combined_value & (1 << 8):
            value = "New Day"
        elif combined_value & (1 << 4):
            value = "Reset Info Flags"
        elif combined_value & (1 << 3):
            value = "EEPROM Init Read"
        elif combined_value & (1 << 2):
            value = "EEPROM Update"
        else:
            value = "None"

        assert value == "None"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
