"""Tests for the available arithmetic operations."""

import pytest

from app.operations import add, subtract


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
