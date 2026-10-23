"""Tests for the programmatic calculator interface."""

import pytest

from app.calculator import Calculator
from app.exceptions import OperationError, ValidationError


def test_successful_calculations_append_one_entry_each():
    calculator = Calculator()
    assert calculator.history == ()
    assert calculator.calculate("add", "2", "3") == 5
    assert calculator.calculate("multiply", 4, 5) == 20
    assert [(entry.operation, entry.first, entry.second, entry.result) for entry in calculator.history] == [
        ("add", 2.0, 3.0, 5.0),
        ("multiply", 4.0, 5.0, 20.0),
    ]


@pytest.mark.parametrize(
    "operation,first,second,error",
    [("add", "bad", 2, ValidationError), ("divide", 2, 0, OperationError), ("unknown", 1, 2, OperationError)],
)
def test_failed_calculation_leaves_history_unchanged(operation, first, second, error):
    calculator = Calculator()
    calculator.calculate("add", 2, 3)
    before = calculator.history
    with pytest.raises(error):
        calculator.calculate(operation, first, second)
    assert calculator.history == before


def test_clear_history():
    calculator = Calculator()
    calculator.calculate("add", 2, 3)
    calculator.clear_history()
    assert calculator.history == ()
