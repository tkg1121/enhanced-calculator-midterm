"""Programmatic calculator interface with in-memory history."""

import os

from app.calculation import Calculation
from app.calculator_memento import CalculatorMemento, UndoRedo
from app.history import History
from app.history_persistence import load_history, save_history


class Calculator:
    """Perform calculations and keep their successful results in order."""

    def __init__(self) -> None:
        self._history = History()
        self._states = UndoRedo()

    @property
    def history(self) -> tuple[Calculation, ...]:
        return self._history.entries()

    def calculate(self, operation: str, first: object, second: object) -> float | int:
        """Return the numeric result and record one successful calculation."""
        entry = Calculation.create(operation, first, second)
        self._states.record(self._snapshot())
        self._history.append(entry)
        return entry.result

    def clear_history(self) -> None:
        """Clear nonempty history as an undoable action."""
        if not self.history:
            return
        self._states.record(self._snapshot())
        self._history.clear()

    def undo(self) -> None:
        """Restore state before the most recent successful change."""
        self._restore(self._states.undo(self._snapshot()))

    def redo(self) -> None:
        """Restore the most recently undone state."""
        self._restore(self._states.redo(self._snapshot()))

    def save_history(self, path: str | os.PathLike[str], encoding: str = "utf-8") -> None:
        """Persist the current state, including after undo, redo, or clear."""
        save_history(self.history, path, encoding)

    def load_history(self, path: str | os.PathLike[str], encoding: str = "utf-8") -> None:
        """Replace history and start a fresh undo/redo baseline after validation."""
        entries = load_history(path, encoding)
        self._history.restore(entries)
        self._states = UndoRedo()

    def _snapshot(self) -> CalculatorMemento:
        return CalculatorMemento(self._history.entries())

    def _restore(self, snapshot: CalculatorMemento) -> None:
        self._history.restore(snapshot.history)
