"""Tests for immutable calculator snapshots and their caretaker."""

import pytest

from app.calculation import Calculation
from app.calculator_memento import CalculatorMemento, UndoRedo
from app.exceptions import OperationError
from app.history import History


def test_snapshot_is_independent_of_later_history_changes():
    history = History()
    first = Calculation.create("add", 2, 3)
    history.append(first)
    snapshot = CalculatorMemento(history.entries())
    history.append(Calculation.create("multiply", 4, 5))

    assert snapshot.history == (first,)
    history.restore(snapshot.history)
    history.clear()
    assert snapshot.history == (first,)


def test_caretaker_moves_snapshots_between_undo_and_redo():
    empty = CalculatorMemento(())
    first = CalculatorMemento((Calculation.create("add", 2, 3),))
    states = UndoRedo()

    states.record(empty)
    assert states.undo(first) == empty
    assert states.redo(empty) == first


def test_record_invalidates_redo():
    empty = CalculatorMemento(())
    first = CalculatorMemento((Calculation.create("add", 2, 3),))
    states = UndoRedo()
    states.record(empty)
    states.undo(first)
    states.record(empty)

    with pytest.raises(OperationError, match="Nothing to redo"):
        states.redo(empty)


def test_empty_stacks_raise_without_changing_state():
    states = UndoRedo()
    empty = CalculatorMemento(())
    with pytest.raises(OperationError, match="Nothing to undo"):
        states.undo(empty)
    with pytest.raises(OperationError, match="Nothing to redo"):
        states.redo(empty)
