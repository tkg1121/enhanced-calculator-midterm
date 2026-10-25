"""Programmatic calculator interface with in-memory history."""

import os
import warnings

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import CalculatorMemento, UndoRedo
from app.history import History
from app.history_persistence import load_history, save_history
from app.exceptions import PersistenceError
from app.logger import Logger
from app.observers import AutoSaveObserver, CalculationObserver, LoggingObserver


class Calculator:
    """Perform calculations and keep their successful results in order."""

    def __init__(
        self,
        log_file: str | os.PathLike[str] | None = None,
        encoding: str | None = None,
        *,
        history_file: str | os.PathLike[str] | None = None,
        auto_save: bool | None = None,
        config: CalculatorConfig | None = None,
    ) -> None:
        log_file = log_file if log_file is not None else config.log_file if config is not None else None
        history_file = history_file if history_file is not None else config.history_file if config is not None else None
        auto_save = auto_save if auto_save is not None else config.auto_save if config is not None else False
        encoding = encoding if encoding is not None else config.encoding if config is not None else "utf-8"
        if auto_save and history_file is None:
            raise ValueError("A history_file path is required when auto_save is enabled.")
        self._history = History(config.max_history_size if config is not None else None)
        self._states = UndoRedo()
        self._observers: list[CalculationObserver] = []
        self._encoding = encoding
        self._max_input_value = config.max_input_value if config is not None else None
        self._precision = config.precision if config is not None else None
        self._history_file = history_file
        self._logger = Logger(log_file, encoding) if log_file is not None else None
        if self._logger is not None:
            self.add_observer(LoggingObserver(self._logger))
        if history_file is not None:
            self.add_observer(AutoSaveObserver(history_file, encoding, enabled=auto_save))

    @property
    def history(self) -> tuple[Calculation, ...]:
        return self._history.entries()

    def calculate(self, operation: str, first: object, second: object) -> float | int:
        """Return the numeric result and record one successful calculation."""
        entry = Calculation.create(
            operation, first, second,
            max_input_value=self._max_input_value, precision=self._precision,
        )
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

    def save_history(self, path: str | os.PathLike[str] | None = None, encoding: str | None = None) -> None:
        """Persist the current state, including after undo, redo, or clear."""
        path = path if path is not None else self._history_file
        if path is None:
            raise ValueError("A history file path is required to save history.")
        try:
            save_history(self.history, path, self._encoding if encoding is None else encoding)
        except PersistenceError as error:
            if self._logger is not None:
                self._logger.error("History save failed for %s: %s", path, error)
            raise
        if self._logger is not None:
            self._logger.info("Saved %s history records to %s", len(self.history), path)

    def load_history(self, path: str | os.PathLike[str] | None = None, encoding: str | None = None) -> None:
        """Replace history and start a fresh undo/redo baseline after validation."""
        path = path if path is not None else self._history_file
        if path is None:
            raise ValueError("A history file path is required to load history.")
        try:
            entries = load_history(path, self._encoding if encoding is None else encoding)
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
