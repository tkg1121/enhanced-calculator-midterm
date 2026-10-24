"""Tests for the programmatic calculator interface."""

import pytest

from app.calculation import Calculation
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


def test_multiple_undo_and_redo_restore_history_without_duplicate_entries():
    calculator = Calculator()
    calculator.calculate("add", 2, 3)
    calculator.calculate("multiply", 4, 5)
    original = calculator.history
    calculator.undo()
    assert [entry.result for entry in calculator.history] == [5]
    calculator.undo()
    assert calculator.history == ()
    calculator.redo()
    assert [entry.result for entry in calculator.history] == [5]
    calculator.redo()
    assert [entry.result for entry in calculator.history] == [5, 20]
    assert calculator.history == original
    assert calculator.history[1] is original[1]


def test_empty_undo_and_redo_raise_existing_custom_error():
    calculator = Calculator()
    with pytest.raises(OperationError, match="Nothing to undo"):
        calculator.undo()
    with pytest.raises(OperationError, match="Nothing to redo"):
        calculator.redo()


def test_new_calculation_after_undo_invalidates_redo():
    calculator = Calculator()
    assert calculator.calculate("add", 2, 3) == 5
    assert calculator.calculate("multiply", 4, 5) == 20
    calculator.undo()
    calculator.redo()
    calculator.undo()
    assert calculator.calculate("subtract", 10, 3) == 7
    assert [entry.result for entry in calculator.history] == [5, 7]
    with pytest.raises(OperationError, match="Nothing to redo"):
        calculator.redo()


@pytest.mark.parametrize(
    "operation,first,second,error",
    [("divide", 2, 0, OperationError), ("add", "bad", 2, ValidationError)],
)
def test_failed_calculation_after_undo_preserves_redo_and_history(operation, first, second, error):
    calculator = Calculator()
    calculator.calculate("add", 2, 3)
    calculator.calculate("multiply", 4, 5)
    calculator.undo()
    before = calculator.history
    with pytest.raises(error):
        calculator.calculate(operation, first, second)
    assert calculator.history == before
    calculator.redo()
    assert [entry.result for entry in calculator.history] == [5, 20]


def test_undo_and_redo_do_not_recalculate(monkeypatch):
    calculator = Calculator()
    calculator.calculate("add", 2, 3)

    def unexpected_calculation(*args, **kwargs):
        raise AssertionError("Undo and redo must restore snapshots")

    monkeypatch.setattr(Calculation, "create", unexpected_calculation)
    calculator.undo()
    calculator.redo()
    assert [entry.result for entry in calculator.history] == [5]


def test_clear_nonempty_history_can_be_undone_and_redone():
    calculator = Calculator()
    calculator.calculate("add", 2, 3)
    calculator.clear_history()
    assert calculator.history == ()
    calculator.undo()
    assert [entry.result for entry in calculator.history] == [5]
    calculator.redo()
    assert calculator.history == ()


def test_clear_nonempty_history_invalidates_previous_redo_branch():
    calculator = Calculator()
    calculator.calculate("add", 2, 3)
    calculator.calculate("multiply", 4, 5)
    calculator.undo()
    calculator.clear_history()
    with pytest.raises(OperationError, match="Nothing to redo"):
        calculator.redo()
    calculator.undo()
    assert [entry.result for entry in calculator.history] == [5]


def test_clearing_empty_history_preserves_stacks():
    calculator = Calculator()
    calculator.clear_history()
    with pytest.raises(OperationError, match="Nothing to undo"):
        calculator.undo()
    calculator.calculate("add", 2, 3)
    calculator.undo()
    calculator.clear_history()
    with pytest.raises(OperationError, match="Nothing to undo"):
        calculator.undo()
    calculator.redo()
    assert [entry.result for entry in calculator.history] == [5]
