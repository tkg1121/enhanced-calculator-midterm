"""Tests for the available arithmetic operations."""

import pytest

from app.operations import add, divide, multiply, subtract


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
    with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
        divide(5, divisor)
