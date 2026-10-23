"""Programmatic calculator interface with in-memory history."""

from app.calculation import Calculation
from app.history import History


class Calculator:
    """Perform calculations and keep their successful results in order."""

    def __init__(self) -> None:
        self._history = History()

    @property
    def history(self) -> tuple[Calculation, ...]:
        return self._history.entries()

    def calculate(self, operation: str, first: object, second: object) -> float | int:
        """Return the numeric result and record one successful calculation."""
        entry = Calculation.create(operation, first, second)
        self._history.append(entry)
        return entry.result

    def clear_history(self) -> None:
        """Clear the current in-memory history."""
        self._history.clear()
