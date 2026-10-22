"""Tests for the available arithmetic operations."""

import pytest

from app.exceptions import CalculatorError, OperationError, ValidationError
from app.operations import (
    abs_diff,
    add,
    divide,
    int_divide,
    modulus,
    multiply,
    percent,
    power,
    root,
    subtract,
)


@pytest.mark.parametrize(
    "first, second, expected",
    [
        (2, 3, 5),
        (-2, 3, 1),
        (0.1, 0.2, 0.3),
    ],
)
def test_add(first, second, expected):
    assert add(first, second) == pytest.approx(expected)


@pytest.mark.parametrize(
    "first, second, expected",
    [
        (5, 2, 3),
        (2, 5, -3),
        (-2, -5, 3),
    ],
)
def test_subtract(first, second, expected):
    assert subtract(first, second) == pytest.approx(expected)


@pytest.mark.parametrize(
    "first, second, expected",
    [
        (4, 3, 12),
        (-4, 3, -12),
        (2.5, 0.2, 0.5),
        (7, 0, 0),
    ],
)
def test_multiply(first, second, expected):
    assert multiply(first, second) == pytest.approx(expected)


@pytest.mark.parametrize(
    "first, second, expected",
    [
        (9, 2, 4.5),
        (-9, 2, -4.5),
        (0, 4, 0),
    ],
)
def test_divide(first, second, expected):
    assert divide(first, second) == pytest.approx(expected)


@pytest.mark.parametrize("divisor", [0, -0.0])
def test_divide_by_zero(divisor):
    with pytest.raises(OperationError, match="Cannot divide by zero"):
        divide(5, divisor)


@pytest.mark.parametrize(
    "base, exponent, expected",
    [
        (2, 3, 8),
        (2, -2, 0.25),
        (-2, 3, -8),
        (4, 0.5, 2),
        (0, 0, 1),
    ],
)
def test_power(base, exponent, expected):
    assert power(base, exponent) == pytest.approx(expected)


@pytest.mark.parametrize(
    "radicand, degree, expected",
    [
        (16, 2, 4),
        (27, 3, 3),
        (-27, 3, -3),
        (-8, -3, -0.5),
        (16, -2, 0.25),
        (0, 3, 0),
    ],
)
def test_root(radicand, degree, expected):
    assert root(radicand, degree) == pytest.approx(expected)


@pytest.mark.parametrize(
    "operation,first,second,message",
    [
        (power, -2, 0.5, "integer exponent"),
        (power, 0, -1, "negative exponent"),
        (power, 1e308, 2, "too large"),
        (root, 8, 0, "cannot be zero"),
        (root, 0, -2, "negative root degree"),
        (root, -16, 2, "odd integer degree"),
        (root, -16, 2.5, "odd integer degree"),
    ],
)
def test_power_and_root_domain_errors(operation, first, second, message):
    with pytest.raises(OperationError, match=message):
        operation(first, second)


@pytest.mark.parametrize(
    "first, second, expected",
    [(7, 3, 1), (-7, 3, 2), (7, -3, -2), (2.5, 1.5, 1.0)],
)
def test_modulus(first, second, expected):
    assert modulus(first, second) == pytest.approx(expected)


@pytest.mark.parametrize(
    "first, second, expected",
    [(7, 2, 3), (-7, 2, -3), (7, -2, -3), (-7, -2, 3), (7.5, 2, 3), (0, 4, 0)],
)
def test_integer_division_truncates_toward_zero(first, second, expected):
    assert int_divide(first, second) == expected


@pytest.mark.parametrize(
    "first, second, expected",
    [(25, 200, 12.5), (-25, 200, -12.5), (0, 5, 0), (1, 3, 100 / 3)],
)
def test_percent(first, second, expected):
    assert percent(first, second) == pytest.approx(expected)


@pytest.mark.parametrize(
    "first, second, expected",
    [(8, 3, 5), (3, 8, 5), (-2, 3, 5), (0.1, 0.3, 0.2)],
)
def test_absolute_difference(first, second, expected):
    assert abs_diff(first, second) == pytest.approx(expected)


@pytest.mark.parametrize("operation", [modulus, int_divide, percent])
def test_new_division_operations_reject_zero_denominator(operation):
    with pytest.raises(OperationError, match="zero"):
        operation(5, 0)


@pytest.mark.parametrize(
    "operation,expected",
    [
        (add, 5),
        (subtract, -1),
        (multiply, 6),
        (divide, 2 / 3),
        (power, 8),
        (root, 2 ** (1 / 3)),
        (modulus, 2),
        (int_divide, 0),
        (percent, 200 / 3),
        (abs_diff, 1),
    ],
)
def test_operations_accept_numeric_strings(operation, expected):
    assert operation("2", "3") == pytest.approx(expected)


@pytest.mark.parametrize(
    "operation",
    [add, subtract, multiply, divide, power, root, modulus, int_divide, percent, abs_diff],
)
@pytest.mark.parametrize("invalid", [None, "bad", True, float("nan"), float("inf")])
def test_operations_reject_invalid_operands(operation, invalid):
    with pytest.raises(ValidationError):
        operation(invalid, 2)
    with pytest.raises(ValidationError):
        operation(2, invalid)


@pytest.mark.parametrize(
    "operation,first,second",
    [
        (add, 1e308, 1e308),
        (subtract, -1e308, 1e308),
        (multiply, 1e308, 2),
        (divide, 1e308, 1e-308),
        (int_divide, 1e308, 1e-308),
        (percent, 1e308, 1e-308),
        (abs_diff, 1e308, -1e308),
        (root, 1e308, 1e-308),
    ],
)
def test_nonfinite_results_raise_operation_error(operation, first, second):
    with pytest.raises(OperationError):
        operation(first, second)


def test_error_types_share_calculator_base():
    assert issubclass(ValidationError, CalculatorError)
    assert issubclass(OperationError, CalculatorError)
