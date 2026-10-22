"""Tests for shared numeric input validation."""

import pytest

from app.exceptions import ValidationError
from app.input_validators import validate_number, validate_operands


@pytest.mark.parametrize(
    "value,expected",
    [(2, 2), (-2.5, -2.5), (" 1e2 ", 100), (0, 0)],
)
def test_valid_numbers(value, expected):
    assert validate_number(value) == expected


@pytest.mark.parametrize(
    "value,message",
    [
        (True, "Boolean"),
        (None, "real number"),
        ("not a number", "real number"),
        (complex(1, 2), "real number"),
        (10 ** 400, "real number"),
        (float("nan"), "finite"),
        (float("inf"), "finite"),
        ("-inf", "finite"),
        ("1e999", "finite"),
    ],
)
def test_invalid_numbers(value, message):
    with pytest.raises(ValidationError, match=message):
        validate_number(value)


def test_both_operands_are_validated():
    assert validate_operands("2", "3.5") == (2.0, 3.5)
    with pytest.raises(ValidationError):
        validate_operands(2, "invalid")
