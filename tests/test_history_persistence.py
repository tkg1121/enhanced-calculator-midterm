"""CSV round trips and failure handling for calculator history."""

import pandas as pd
import pytest
from datetime import datetime

from app.calculation import Calculation

from app.calculator import Calculator
from app.exceptions import OperationError, PersistenceError


def test_round_trip_preserves_order_values_types_and_timestamps(tmp_path):
    original = Calculator()
    original.calculate("add", 2.5, 3)
    original.calculate("int_divide", 7, 2)
    expected = original.history
    path = tmp_path / "nested" / "history.csv"
    original.save_history(path)

    frame = pd.read_csv(path, dtype=str)
    assert list(frame.columns) == ["operation", "first", "second", "result", "timestamp"]
    assert frame["result"].tolist() == ["5.5", "3"]
    assert frame["timestamp"].tolist() == [entry.timestamp.isoformat() for entry in expected]
    restored = Calculator()
    restored.load_history(path)
    assert restored.history == expected
    assert type(restored.history[1].result) is int


def test_empty_history_writes_headers_and_loads(tmp_path):
    path = tmp_path / "empty.csv"
    Calculator().save_history(path)
    assert path.read_text(encoding="utf-8").strip() == "operation,first,second,result,timestamp"
    calculator = Calculator()
    calculator.calculate("add", 1, 2)
    calculator.load_history(path)
    assert calculator.history == ()


def test_manual_save_uses_current_state_after_undo_redo_and_clear(tmp_path):
    calculator = Calculator()
    calculator.calculate("add", 2, 3)
    calculator.calculate("multiply", 4, 5)
    calculator.undo()
    path = tmp_path / "history.csv"
    calculator.save_history(path)
    loaded = Calculator()
    loaded.load_history(path)
    assert [entry.result for entry in loaded.history] == [5]
    calculator.redo()
    calculator.save_history(path)
    loaded.load_history(path)
    assert [entry.result for entry in loaded.history] == [5, 20]
    calculator.clear_history()
    calculator.save_history(path)
    loaded.load_history(path)
    assert loaded.history == ()


@pytest.mark.parametrize(
    "content,match",
    [
        ("not,a,valid,header\n", "missing columns"),
        ("operation,first,second,result,timestamp\nadd,1,2,3,2026-10-23T00:00:00+00:00,extra\n", "Could not load"),
        ("operation,first,second,result,timestamp\nunknown,1,2,3,2026-10-23T00:00:00+00:00\n", "row 2"),
        ("operation,first,second,result,timestamp\nadd,bad,2,3,2026-10-23T00:00:00+00:00\n", "row 2"),
        ("operation,first,second,result,timestamp\nadd,1,2,4,2026-10-23T00:00:00+00:00\n", "row 2"),
        ("operation,first,second,result,timestamp\nadd,1,2,3,not-a-date\n", "row 2"),
        ("operation,first,second,result,timestamp\nadd,1,2,3,2026-10-23T00:00:00\n", "row 2"),
    ],
)
def test_invalid_csv_is_rejected_without_changing_state(tmp_path, content, match):
    path = tmp_path / "bad.csv"
    path.write_text(content, encoding="utf-8")
    calculator = Calculator()
    calculator.calculate("add", 2, 3)
    calculator.calculate("multiply", 4, 5)
    calculator.undo()
    before = calculator.history
    with pytest.raises(PersistenceError, match=match):
        calculator.load_history(path)
    assert calculator.history == before
    calculator.redo()
    assert [entry.result for entry in calculator.history] == [5, 20]
    calculator.undo()
    assert calculator.history == before


def test_missing_file_raises_application_error(tmp_path):
    with pytest.raises(PersistenceError, match="Could not load"):
        Calculator().load_history(tmp_path / "missing.csv")


def test_valid_row_before_invalid_row_does_not_partially_load(tmp_path):
    path = tmp_path / "history.csv"
    path.write_text(
        "operation,first,second,result,timestamp\n"
        "add,1,2,3,2026-10-23T00:00:00+00:00\n"
        "divide,1,0,0,2026-10-23T00:00:01+00:00\n",
        encoding="utf-8",
    )
    calculator = Calculator()
    calculator.calculate("subtract", 8, 2)
    before = calculator.history
    with pytest.raises(PersistenceError, match="row 3"):
        calculator.load_history(path)
    assert calculator.history == before
    calculator.undo()
    assert calculator.history == ()


def test_loaded_offset_timestamp_is_normalized_to_utc(tmp_path):
    path = tmp_path / "history.csv"
    path.write_text(
        "operation,first,second,result,timestamp\n"
        "add,1,2,3,2026-10-23T02:00:00+02:00\n", encoding="utf-8",
    )
    calculator = Calculator()
    calculator.load_history(path)
    assert calculator.history[0].timestamp.isoformat() == "2026-10-23T00:00:00+00:00"


def test_successful_load_resets_undo_and_redo_baseline(tmp_path):
    source = Calculator()
    source.calculate("subtract", 8, 3)
    path = tmp_path / "history.csv"
    source.save_history(path)
    target = Calculator()
    target.calculate("add", 2, 3)
    target.calculate("multiply", 4, 5)
    target.undo()
    target.load_history(path)
    assert target.history == source.history
    with pytest.raises(OperationError, match="Nothing to undo"):
        target.undo()
    with pytest.raises(OperationError, match="Nothing to redo"):
        target.redo()


def test_failed_write_preserves_existing_file_and_removes_temporary(tmp_path, monkeypatch):
    path = tmp_path / "history.csv"
    calculator = Calculator()
    calculator.calculate("add", 2, 3)
    calculator.save_history(path)
    before = path.read_bytes()

    def fail_write(self, stream, **kwargs):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(pd.DataFrame, "to_csv", fail_write)
    with pytest.raises(PersistenceError, match="simulated disk failure"):
        calculator.save_history(path)
    assert path.read_bytes() == before
    assert list(tmp_path.glob("*.tmp")) == []


def test_replace_failure_preserves_existing_file(tmp_path, monkeypatch):
    path = tmp_path / "history.csv"
    calculator = Calculator()
    calculator.calculate("add", 2, 3)
    calculator.save_history(path)
    before = path.read_bytes()

    def fail_replace(source, destination):
        raise PermissionError("simulated permission failure")

    monkeypatch.setattr("app.history_persistence.os.replace", fail_replace)
    with pytest.raises(PersistenceError, match="permission failure"):
        calculator.save_history(path)
    assert path.read_bytes() == before


def test_naive_record_timestamp_is_not_saved(tmp_path):
    from app.history_persistence import save_history

    record = Calculation("add", 1.0, 2.0, 3.0, datetime(2026, 10, 23))
    with pytest.raises(PersistenceError, match="timezone offset"):
        save_history((record,), tmp_path / "history.csv")
