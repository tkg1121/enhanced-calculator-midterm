"""Programmatic calculator interface with in-memory history."""

import os
import warnings

from app.calculation import Calculation
from app.calculator_memento import CalculatorMemento, UndoRedo
from app.history import History
from app.history_persistence import load_history, save_history
from app.exceptions import PersistenceError
from app.logger import Logger
from app.observers import CalculationObserver, LoggingObserver


class Calculator:
    """Perform calculations and keep their successful results in order."""

    def __init__(self, log_file: str | os.PathLike[str] | None = None, encoding: str = "utf-8") -> None:
        self._history = History()
        self._states = UndoRedo()
        self._observers: list[CalculationObserver] = []
        self._logger = Logger(log_file, encoding) if log_file is not None else None
        if self._logger is not None:
            self.add_observer(LoggingObserver(self._logger))

    @property
    def history(self) -> tuple[Calculation, ...]:
        return self._history.entries()

    def calculate(self, operation: str, first: object, second: object) -> float | int:
        """Return the numeric result and record one successful calculation."""
        entry = Calculation.create(operation, first, second)
        self._states.record(self._snapshot())
        self._history.append(entry)
        self._notify(entry)
        return entry.result

    def add_observer(self, observer: CalculationObserver) -> None:
        """Register an observer once by object identity."""
        if not any(existing is observer for existing in self._observers):
            self._observers.append(observer)

    def remove_observer(self, observer: CalculationObserver) -> None:
        """Remove a registered observer; a missing observer is a no-op."""
        self._observers = [existing for existing in self._observers if existing is not observer]

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
        try:
            save_history(self.history, path, encoding)
        except PersistenceError as error:
            if self._logger is not None:
                self._logger.error("History save failed for %s: %s", path, error)
            raise
        if self._logger is not None:
            self._logger.info("Saved %s history records to %s", len(self.history), path)

    def load_history(self, path: str | os.PathLike[str], encoding: str = "utf-8") -> None:
        """Replace history and start a fresh undo/redo baseline after validation."""
        try:
            entries = load_history(path, encoding)
        except PersistenceError as error:
            if self._logger is not None:
                self._logger.error("History load failed for %s: %s", path, error)
            raise
        self._history.restore(entries)
        self._states = UndoRedo()
        if self._logger is not None:
            self._logger.info("Loaded %s history records from %s", len(entries), path)

    def _notify(self, entry: Calculation) -> None:
        for observer in tuple(self._observers):
            try:
                observer.on_calculation(entry, self)
            except (PersistenceError, OSError) as error:
                message = f"Calculation observer {type(observer).__name__} failed: {error}"
                if self._logger is not None:
                    self._logger.warning("%s", message)
                warnings.warn(message, RuntimeWarning, stacklevel=2)

    def _snapshot(self) -> CalculatorMemento:
        return CalculatorMemento(self._history.entries())

    def _restore(self, snapshot: CalculatorMemento) -> None:
        self._history.restore(snapshot.history)
