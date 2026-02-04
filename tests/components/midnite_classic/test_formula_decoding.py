"""Tests for formula decoding/correction in midnite_classic integration.

This module tests that formulas are correctly applied to convert raw register values
to their final display values. The key issue being tested is that formulas must use
the assignment syntax 'value = value / 60.0' rather than just an expression like
'value / 60.0' for the result to be captured correctly.
"""

from __future__ import annotations

import pytest


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


def _apply_formula(formula: str, value: float) -> float | None:
    """Apply a formula to a raw register value.

    This mimics what happens in DynamicSensor._apply_formula() when exec()
    is called with the formula string.
    """
    local_vars = {"value": value}

    # Normalize and strip whitespace from formula
    formula_str = _normalize_formula_indentation(formula).strip()

    try:
        exec(  # noqa: S102
            compile(formula_str, "<string>", "exec"),
            {"__name__": "__main__"},
            local_vars,
        )
        return local_vars.get("value")
    except Exception:  # noqa: BLE001
        return None


class TestFormulaExecution:
    """Test formula execution logic."""

    def test_time_seconds_to_minutes_conversion(self) -> None:
        """Test that raw seconds are correctly converted to minutes."""
        formula = "value = value / 60.0"

        # Test cases: (raw_value, expected_minutes)
        test_cases = [
            (0, 0.0),
            (60, 1.0),  # 60 seconds = 1 minute
            (300, 5.0),  # 300 seconds = 5 minutes
            (600, 10.0),  # 600 seconds = 10 minutes
            (1800, 30.0),  # 1800 seconds = 30 minutes
            (3600, 60.0),  # 3600 seconds = 60 minutes (1 hour)
            (7200, 120.0),  # 7200 seconds = 120 minutes (2 hours)
            (18000, 300.0),  # 18000 seconds = 300 minutes (5 hours)
        ]

        for raw_value, expected_minutes in test_cases:
            result = _apply_formula(formula, raw_value)
            assert result == expected_minutes, (
                f"Failed for {raw_value} seconds: "
                f"expected {expected_minutes} min, got {result}"
            )

    def test_voltage_current_scaling(self) -> None:
        """Test that voltage/current values are correctly scaled by /10."""
        formula = "value = value / 10.0"

        # Test cases: (raw_value, expected_scaled)
        test_cases = [
            (0, 0.0),
            (10, 1.0),  # 10 raw = 1.0 scaled
            (100, 10.0),  # 100 raw = 10.0 scaled
            (245, 24.5),  # 245 raw = 24.5 scaled
            (500, 50.0),  # 500 raw = 50.0 scaled
            (1000, 100.0),  # 1000 raw = 100.0 scaled
        ]

        for raw_value, expected_scaled in test_cases:
            result = _apply_formula(formula, raw_value)
            assert result == expected_scaled, (
                f"Failed for {raw_value} raw: expected {expected_scaled}, got {result}"
            )

    def test_signed_16bit_formula(self) -> None:
        """Test signed 16-bit value handling from current_voltage.py pattern.

        Note: The original formula has a logic issue - it checks if the scaled
        value (after /10.0) is > 32767, but since raw values max at 65535,
        this can never be true for practical values. The test verifies that
        positive values work and out-of-range values return None.
        """
        formula = """
            current_value = value / 10.0
            if current_value > 32767:
                current_value = current_value - 65536
            value = current_value if abs(current_value) <= 100 else None
        """

        # Positive value: 245 raw = 24.5A
        result = _apply_formula(formula, 245)
        assert result == 24.5

        # Value exceeding limit: 1500 raw = 150A > 100 limit
        result = _apply_formula(formula, 1500)
        assert result is None

    def test_no_assignment_formula_returns_original(self) -> None:
        """Test that a formula without assignment returns the original value."""
        # This demonstrates the BUG: formulas like "value / 60.0" without assignment
        # will not update the 'value' variable in local_vars
        formula = "value / 60.0"

        raw_value = 1800
        result = _apply_formula(formula, raw_value)

        # Without assignment, the original value is returned (not converted)
        assert result == raw_value, (
            f"Formula without assignment should return original value. "
            f"Expected {raw_value}, got {result}"
        )


class TestTimeSettingsFormulas:
    """Test time settings formulas specifically."""

    @pytest.mark.parametrize(
        ("raw_value", "expected_minutes"),
        [
            (0, 0.0),
            (60, 1.0),  # 60 seconds = 1 minute
            (300, 5.0),  # 300 seconds = 5 minutes
            (600, 10.0),  # 600 seconds = 10 minutes
            (1800, 30.0),  # 1800 seconds = 30 minutes
            (3600, 60.0),  # 3600 seconds = 60 minutes (1 hour)
            (7200, 120.0),  # 7200 seconds = 120 minutes (2 hours)
            (18000, 300.0),  # 18000 seconds = 300 minutes (5 hours)
        ],
    )
    def test_time_settings_division(
        self, raw_value: int, expected_minutes: float
    ) -> None:
        """Test that time settings correctly convert seconds to minutes."""
        formula = "value = value / 60.0"
        local_vars = {"value": raw_value}
        exec(compile(formula, "<string>", "exec"), {"__name__": "__main__"}, local_vars)  # noqa: S102
        assert local_vars["value"] == expected_minutes


class TestScalingFormulas:
    """Test scaling formulas for voltage/current sensors."""

    @pytest.mark.parametrize(
        ("raw_value", "expected_scaled"),
        [
            (0, 0.0),
            (10, 1.0),  # 10 raw = 1.0 scaled
            (100, 10.0),  # 100 raw = 10.0 scaled
            (245, 24.5),  # 245 raw = 24.5 scaled
            (500, 50.0),  # 500 raw = 50.0 scaled
            (1000, 100.0),  # 1000 raw = 100.0 scaled
            (6553, 655.3),  # Large value
        ],
    )
    def test_divide_by_10_scaling(self, raw_value: int, expected_scaled: float) -> None:
        """Test that values are correctly scaled by dividing by 10."""
        formula = "value = value / 10.0"
        local_vars = {"value": raw_value}
        exec(compile(formula, "<string>", "exec"), {"__name__": "__main__"}, local_vars)  # noqa: S102
        assert local_vars["value"] == expected_scaled


class TestFormulaNormalization:
    """Test formula string normalization."""

    def test_simple_expression_without_assignment(self) -> None:
        """Test that a simple expression like 'value / 60.0' is normalized."""
        formula = "value / 60.0"
        result = _normalize_formula_indentation(formula)
        # The function should normalize indentation but not add assignment
        assert "value / 60.0" in result

    def test_expression_with_assignment(self) -> None:
        """Test that 'value = value / 60.0' is preserved."""
        formula = "value = value / 60.0"
        result = _normalize_formula_indentation(formula)
        assert "value = value / 60.0" in result

    def test_multiline_formula(self) -> None:
        """Test multiline formula normalization."""
        formula = """
            current_value = value / 10.0
            if current_value > 32767:
                current_value = current_value - 65536
            value = current_value if abs(current_value) <= 100 else None
        """
        result = _normalize_formula_indentation(formula)
        # Should normalize indentation
        assert "current_value = value / 10.0" in result
        assert "value = current_value" in result

    def test_return_statement_replacement(self) -> None:
        """Test that 'return' is replaced with 'value ='."""
        formula = "return value / 60.0"
        result = _normalize_formula_indentation(formula)
        assert "value = value / 60.0" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
