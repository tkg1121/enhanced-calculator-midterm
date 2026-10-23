"""Tests for immutable calculation records."""

from dataclasses import FrozenInstanceError

import pytest

from app.calculation import Calculation
from app.exceptions import OperationError, ValidationError


@pytest.mark.parametrize(
    "name,first,second,expected",
    [(" ADD ", "2", "3", 5), ("int_divide", -7, 2, -3), ("root", -27, 3, -3)],
)
def test_create_completed_record(name, first, second, expected):
    record = Calculation.create(name, first, second)
    assert record.operation == name.strip().lower()
    assert record.first == float(first)
    assert record.second == float(second)
    assert record.result == pytest.approx(expected)


def test_record_cannot_be_changed():
    record = Calculation.create("add", 2, 3)
    with pytest.raises(FrozenInstanceError):
        record.result = 999


@pytest.mark.parametrize(
    "name,first,second,error",
    [("unknown", 1, 2, OperationError), ("add", "bad", 2, ValidationError), ("divide", 2, 0, OperationError)],
)
def test_failed_calculation_does_not_create_record(name, first, second, error):
    with pytest.raises(error):
        Calculation.create(name, first, second)
