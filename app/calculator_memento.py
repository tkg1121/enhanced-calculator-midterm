"""Snapshots and undo/redo bookkeeping for calculator history."""

from dataclasses import dataclass

from app.calculation import Calculation
from app.exceptions import OperationError


@dataclass(frozen=True)
class CalculatorMemento:
    """An immutable snapshot of the calculator's completed calculations."""

    history: tuple[Calculation, ...]


class UndoRedo:
    """Keep prior and undone snapshots without owning calculator state."""

    def __init__(self) -> None:
        self._undo: list[CalculatorMemento] = []
        self._redo: list[CalculatorMemento] = []

    def record(self, current: CalculatorMemento) -> None:
        """Save state before a successful change and discard the old redo branch."""
        self._undo.append(current)
        self._redo.clear()

    def undo(self, current: CalculatorMemento) -> CalculatorMemento:
        if not self._undo:
            raise OperationError("Nothing to undo.")
        self._redo.append(current)
        return self._undo.pop()

    def redo(self, current: CalculatorMemento) -> CalculatorMemento:
        if not self._redo:
            raise OperationError("Nothing to redo.")
        self._undo.append(current)
        return self._redo.pop()
