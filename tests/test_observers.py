"""Calculation notifications and file logging."""

import logging

import pytest

from app.calculator import Calculator
from app.exceptions import OperationError, PersistenceError, ValidationError
from app.logger import Logger


class RecordingObserver:
    def __init__(self):
        self.calls = []

    def on_calculation(self, calculation, calculator):
        self.calls.append((calculation, calculator.history))


def test_observer_receives_one_completed_record_after_history_update():
    calculator = Calculator()
    observer = RecordingObserver()
    calculator.add_observer(observer)
    calculator.add_observer(observer)
    calculator.calculate("add", 2, 3)
    assert len(observer.calls) == 1
    record, history_at_notification = observer.calls[0]
    assert record is calculator.history[0]
    assert history_at_notification == calculator.history
    calculator.undo()
    calculator.redo()
    assert len(observer.calls) == 1


def test_removed_observer_receives_no_more_notifications():
    calculator = Calculator()
    observer = RecordingObserver()
    calculator.add_observer(observer)
    calculator.remove_observer(observer)
    calculator.remove_observer(observer)
    calculator.calculate("add", 2, 3)
    assert observer.calls == []


def test_failed_calculations_do_not_notify():
    calculator = Calculator()
    observer = RecordingObserver()
    calculator.add_observer(observer)
    with pytest.raises(ValidationError):
        calculator.calculate("add", "bad", 2)
    with pytest.raises(OperationError):
        calculator.calculate("divide", 2, 0)
    assert observer.calls == []


def test_clear_and_load_do_not_notify(tmp_path):
    calculator = Calculator()
    observer = RecordingObserver()
    calculator.add_observer(observer)
    calculator.calculate("add", 2, 3)
    path = tmp_path / "history.csv"
    calculator.save_history(path)
    calculator.clear_history()
    calculator.load_history(path)
    assert len(observer.calls) == 1


def test_file_io_observer_failure_warns_and_allows_following_observers():
    calculator = Calculator()

    class FailingObserver:
        def on_calculation(self, calculation, owner):
            raise PersistenceError("simulated write failure")

    recorder = RecordingObserver()
    calculator.add_observer(FailingObserver())
    calculator.add_observer(recorder)
    with pytest.warns(RuntimeWarning, match="simulated write failure"):
        assert calculator.calculate("add", 2, 3) == 5
    assert len(calculator.history) == 1
    assert len(recorder.calls) == 1
    calculator.undo()
    assert calculator.history == ()


def test_observer_file_io_failure_is_logged_and_other_observers_run(tmp_path):
    calculator = Calculator(log_file=tmp_path / "calculator.log")

    class FailingObserver:
        def on_calculation(self, calculation, owner):
            raise OSError("simulated file error")

    recorder = RecordingObserver()
    calculator.add_observer(FailingObserver())
    calculator.add_observer(recorder)
    with pytest.warns(RuntimeWarning, match="simulated file error"):
        calculator.calculate("add", 2, 3)
    assert len(recorder.calls) == 1
    assert " WARNING Calculation observer FailingObserver failed: simulated file error" in (
        tmp_path / "calculator.log"
    ).read_text(encoding="utf-8")


def test_programming_errors_from_observers_are_not_hidden():
    calculator = Calculator()

    class BrokenObserver:
        def on_calculation(self, calculation, owner):
            raise RuntimeError("broken observer code")

    calculator.add_observer(BrokenObserver())
    with pytest.raises(RuntimeError, match="broken observer code"):
        calculator.calculate("add", 2, 3)
    assert len(calculator.history) == 1


def test_logging_observer_records_details_once_with_two_calculators(tmp_path):
    path = tmp_path / "calculator.log"
    first = Calculator(log_file=path)
    second = Calculator(log_file=path)
    first.calculate("add", 2, 3)
    second.calculate("subtract", 8, 5)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert sum("Calculated add(2.0, 3.0) = 5.0" in line for line in lines) == 1
    assert sum("Calculated subtract(8.0, 5.0) = 3.0" in line for line in lines) == 1
    assert all(" INFO " in line for line in lines)
    logger = Logger(path)
    assert sum(isinstance(handler, logging.FileHandler) for handler in logger._logger.handlers) == 1


def test_persistence_errors_and_successes_are_logged(tmp_path):
    path = tmp_path / "calculator.log"
    calculator = Calculator(log_file=path)
    with pytest.raises(PersistenceError):
        calculator.load_history(tmp_path / "missing.csv")
    calculator.calculate("add", 2, 3)
    history_path = tmp_path / "history.csv"
    calculator.save_history(history_path)
    calculator.load_history(history_path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert any(" ERROR History load failed" in line for line in lines)
    assert any(" INFO Saved 1 history records" in line for line in lines)
    assert any(" INFO Loaded 1 history records" in line for line in lines)


def test_manual_save_failure_is_logged(tmp_path, monkeypatch):
    calculator = Calculator(log_file=tmp_path / "calculator.log")

    def fail_save(*args, **kwargs):
        raise PersistenceError("simulated save error")

    monkeypatch.setattr("app.calculator.save_history", fail_save)
    with pytest.raises(PersistenceError, match="simulated save error"):
        calculator.save_history(tmp_path / "history.csv")
    assert " ERROR History save failed" in (tmp_path / "calculator.log").read_text(encoding="utf-8")
