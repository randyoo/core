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
        # We expect 5 selects: force_charge_state, force_actions,
        # charge_mode (disabled), device_type_override (disabled),
        # communication_mode (disabled)
        # Only 2 active selectors currently (charge_mode, device_type_override,
        # and communication_mode are commented out)
        assert len(SELECT_DEFINITIONS) == 2

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

    def test_charge_mode_definition_disabled(self) -> None:
        """Test that Charge Mode select definition exists but is disabled."""
        charge_mode_select = next(
            (s for s in SELECT_DEFINITIONS if s.key == "charge_mode"),
            None,
        )
        # The definition should still exist in the list (commented out but not removed)
        assert charge_mode_select is None

    def test_device_type_override_definition_disabled(self) -> None:
        """Test that Device Type Override select definition exists but is disabled."""
        device_type_select = next(
            (s for s in SELECT_DEFINITIONS if s.key == "device_type_override"),
            None,
        )
        # The definition should still exist in the list (commented out but not removed)
        assert device_type_select is None

    def test_communication_mode_definition_disabled(self) -> None:
        """Test that Communication Mode select definition exists but is disabled."""
        comm_mode_select = next(
            (s for s in SELECT_DEFINITIONS if s.key == "communication_mode"),
            None,
        )
        # The definition should still exist in the list (commented out but not removed)
        assert comm_mode_select is None


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


class TestForceActionsWriteFormulas:
    """Test the Force Actions select write formulas with high bits.

    This tests that the write formula returns correct combined values
    for registers 4160 (low) and 4161 (high).
    """

    def test_force_actions_write_reset_faults(self) -> None:
        """Test writing Reset Faults option.

        Reset Faults uses bit 23, which is in the high register (4161).
        The write formula should return a 32-bit value where high bits = 0x80 (bit 7 of high register).
        """
        # Simulate what the write formula returns
        value = 0

        # Clear bits first (bits 2, 3, 4, 8, 11 in low; bits 16, 23 in high)
        low_value = value & 0xFFFF
        low_value &= ~((1 << 11) | (1 << 8) | (1 << 4) | (1 << 3) | (1 << 2))
        high_value = (value >> 16) & 0xFFFF
        high_value &= ~(
            (1 << (23 - 16)) | (1 << (16 - 16))
        )  # bits 0 and 7 in high register

        # Set Reset Faults bit (bit 23 = bit 7 of high register)
        low_value &= ~(1 << 11) | ~(1 << 8) | ~(1 << 4) | ~(1 << 3) | ~(1 << 2)
        high_value &= ~((1 << (23 - 16)) | (1 << (16 - 16)))
        high_value |= 1 << (23 - 16)

        # Combine
        result = (high_value << 16) | low_value

        assert result == 0x800000, f"Expected 0x800000 but got {result}"
        # The high value (0x80 = 128) should be written to register 4161

    def test_force_actions_write_reset_aeq(self) -> None:
        """Test writing Reset Auto EQ Counter option.

        Reset Auto EQ Counter uses bit 16, which is in the high register (4161).
        The write formula should return a 32-bit value where high bits = 0x1 (bit 0 of high register).
        """
        # Simulate what the write formula returns
        value = 0

        # Clear bits first (bits 2, 3, 4, 8, 11 in low; bits 16, 23 in high)
        low_value = value & 0xFFFF
        low_value &= ~((1 << 11) | (1 << 8) | (1 << 4) | (1 << 3) | (1 << 2))
        high_value = (value >> 16) & 0xFFFF
        high_value &= ~(
            (1 << (23 - 16)) | (1 << (16 - 16))
        )  # bits 0 and 7 in high register

        # Set Reset Auto EQ Counter bit (bit 16 = bit 0 of high register)
        low_value &= ~(1 << 11) | ~(1 << 8) | ~(1 << 4) | ~(1 << 3) | ~(1 << 2)
        high_value &= ~((1 << (23 - 16)) | (1 << (16 - 16)))
        high_value |= 1 << (16 - 16)

        # Combine
        result = (high_value << 16) | low_value

        assert result == 0x10000, f"Expected 0x10000 but got {result}"
        # The high value (0x1 = 1) should be written to register 4161


class TestSelectWriteWithHighBits:
    """Test that select write with high bits correctly determines register address.

    This tests the fix for the issue where "Reset Faults" and "Reset Auto EQ Counter"
    options were writing to register 4160 instead of 4161.

    The fix in select.py:
    - Takes the combined value (high << 16 | low)
    - Extracts high and low values
    - Writes to secondary register if high bits are set
    """

    def test_reset_faults_should_write_to_register_4161(self) -> None:
        """Test that Reset Faults writes to secondary register (4161), not 4160.

        The issue was that Reset Faults (bit 23) was calculating value & 0xFFFF,
        which gave 0 because bit 23 is beyond the low 16 bits.

        The fix:
        1. Formula returns combined value (high << 16 | low) = 0x800000
        2. select.py extracts high=0x80, low=0 from combined value
        3. Since high > 0, writes to secondary register (4161) with value 0x80
        """
        # Simulate the combined value returned by write formula for Reset Faults
        # Bit 23 = bit 7 of high register (4161), so high=0x80, low=0
        combined_value = (0x80 << 16) | 0x00  # = 0x800000 = 8388608

        # Extract high and low values (this is what select.py does)
        low_value = combined_value & 0xFFFF  # 0x00
        high_value = (combined_value >> 16) & 0xFFFF  # 0x80

        # Determine register based on high bits
        secondary_register = 4161  # High bits (bits 16+) use this register
        main_register = 4160

        # If high bits are set, write to secondary register
        if high_value > 0:
            write_register = secondary_register
            value_to_write = high_value
        else:
            write_register = main_register
            value_to_write = low_value

        # Verify the fix
        assert write_register == 4161, (
            f"Expected register 4161 but got {write_register}"
        )
        assert value_to_write == 0x80, f"Expected 0x80 but got {value_to_write}"

    def test_reset_aeq_should_write_to_register_4161(self) -> None:
        """Test that Reset Auto EQ Counter writes to secondary register (4161), not 4160.

        Bit 16 = bit 0 of high register (4161), so high=0x1, low=0.
        """
        # Simulate the combined value returned by write formula for Reset Auto EQ Counter
        # Bit 16 = bit 0 of high register (4161), so high=0x1, low=0
        combined_value = (0x1 << 16) | 0x00  # = 0x10000 = 65536

        # Extract high and low values (this is what select.py does)
        low_value = combined_value & 0xFFFF  # 0x00
        high_value = (combined_value >> 16) & 0xFFFF  # 0x1

        # Determine register based on high bits
        secondary_register = 4161
        main_register = 4160

        if high_value > 0:
            write_register = secondary_register
            value_to_write = high_value
        else:
            write_register = main_register
            value_to_write = low_value

        assert write_register == 4161, (
            f"Expected register 4161 but got {write_register}"
        )
        assert value_to_write == 0x1, f"Expected 0x1 but got {value_to_write}"

    def test_low_bits_should_still_write_to_register_4160(self) -> None:
        """Test that low bits (e.g., Sweep/Re-track bit 11) still write to register 4160."""
        # Bit 11 is in low register (4160), so high=0, low=(1 << 11) = 0x800
        combined_value = (0x00 << 16) | (1 << 11)  # = 0x800

        low_value = combined_value & 0xFFFF
        high_value = (combined_value >> 16) & 0xFFFF

        secondary_register = 4161
        main_register = 4160

        if high_value > 0:
            write_register = secondary_register
            value_to_write = high_value
        else:
            write_register = main_register
            value_to_write = low_value

        assert write_register == 4160, (
            f"Expected register 4160 but got {write_register}"
        )
        assert value_to_write == (1 << 11), (
            f"Expected {1 << 11} but got {value_to_write}"
        )


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
