"""Automatic history saving through the calculation observer."""

import pytest

from app.calculator import Calculator
from app.exceptions import PersistenceError
from app.observers import AutoSaveObserver


def test_auto_save_writes_complete_history_after_each_success(tmp_path):
    path = tmp_path / "nested" / "history.csv"
    calculator = Calculator(history_file=path, auto_save=True)
    calculator.calculate("add", 2, 3)
    first = Calculator()
    first.load_history(path)
    assert first.history == calculator.history
    calculator.calculate("multiply", 4, 5)
    second = Calculator()
    second.load_history(path)
    assert second.history == calculator.history
    assert [entry.result for entry in second.history] == [5, 20]


def test_auto_save_disabled_does_not_write_file(tmp_path):
    path = tmp_path / "history.csv"
    calculator = Calculator(history_file=path, auto_save=False)
    calculator.calculate("add", 2, 3)
    assert not path.exists()
    calculator.save_history(path)
    assert path.exists()


def test_auto_save_observer_can_be_enabled_or_disabled(tmp_path):
    path = tmp_path / "history.csv"
    observer = AutoSaveObserver(path, enabled=False)
    calculator = Calculator()
    calculator.add_observer(observer)
    calculator.calculate("add", 2, 3)
    assert not path.exists()
    observer.enabled = True
    calculator.calculate("multiply", 4, 5)
    loaded = Calculator()
    loaded.load_history(path)
    assert loaded.history == calculator.history
    observer.enabled = False
    calculator.calculate("subtract", 10, 3)
    loaded.load_history(path)
    assert len(loaded.history) == 2


def test_auto_save_only_responds_to_new_calculations(tmp_path):
    path = tmp_path / "history.csv"
    calculator = Calculator(history_file=path, auto_save=True)
    calculator.calculate("add", 2, 3)
    original = path.read_bytes()
    calculator.undo()
    calculator.redo()
    calculator.clear_history()
    calculator.load_history(path)
    assert path.read_bytes() == original


def test_auto_save_failure_keeps_successful_calculation_and_warns(tmp_path, monkeypatch):
    path = tmp_path / "history.csv"
    calculator = Calculator(history_file=path, auto_save=True)

    def fail_save(*args, **kwargs):
        raise PersistenceError("simulated auto-save failure")

    monkeypatch.setattr("app.calculator.save_history", fail_save)
    with pytest.warns(RuntimeWarning, match="simulated auto-save failure"):
        assert calculator.calculate("add", 2, 3) == 5
    assert len(calculator.history) == 1
    calculator.undo()
    assert calculator.history == ()
    calculator.redo()
    assert [entry.result for entry in calculator.history] == [5]


def test_failed_auto_save_preserves_previous_valid_csv(tmp_path, monkeypatch):
    path = tmp_path / "history.csv"
    calculator = Calculator(history_file=path, auto_save=True)
    calculator.calculate("add", 2, 3)
    original = path.read_bytes()

    def fail_replace(*args, **kwargs):
        raise OSError("simulated replace error")

    monkeypatch.setattr("app.history_persistence.os.replace", fail_replace)
    with pytest.warns(RuntimeWarning, match="simulated replace error"):
        calculator.calculate("multiply", 4, 5)
    assert [entry.result for entry in calculator.history] == [5, 20]
    assert path.read_bytes() == original


def test_constructor_encoding_applies_to_automatic_csv_and_logging(tmp_path):
    history = tmp_path / "history.csv"
    log = tmp_path / "calculator.log"
    calculator = Calculator(log_file=log, encoding="utf-16", history_file=history, auto_save=True)
    calculator.calculate("add", 2, 3)
    restored = Calculator()
    restored.load_history(history, encoding="utf-16")
    assert restored.history == calculator.history
    assert "Calculated add" in log.read_text(encoding="utf-16")


def test_auto_save_requires_history_path():
    with pytest.raises(ValueError, match="history_file"):
        Calculator(auto_save=True)
