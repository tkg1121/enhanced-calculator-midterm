"""Integration of validated settings with calculation and persistence."""

import pytest

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app.exceptions import ConfigurationError, OperationError, PersistenceError, ValidationError


def configured(tmp_path, **overrides):
    return CalculatorConfig.load(base_dir=tmp_path, environ={}, overrides=overrides)


@pytest.mark.parametrize("boundary", [10, -10])
def test_input_limit_accepts_both_boundaries(tmp_path, boundary):
    config = configured(tmp_path, CALCULATOR_MAX_INPUT_VALUE="10")
    calculator = Calculator(config=config)
    assert calculator.calculate("add", boundary, 0) == boundary


@pytest.mark.parametrize("outside", [10.0001, -10.0001])
def test_input_limit_rejects_both_sides_without_changing_history_or_redo(tmp_path, outside):
    config = configured(tmp_path, CALCULATOR_MAX_INPUT_VALUE="10")
    calculator = Calculator(config=config)
    calculator.calculate("add", 1, 2)
    calculator.calculate("add", 3, 4)
    calculator.undo()
    before = calculator.history

    class Recorder:
        calls = 0

        def on_calculation(self, calculation, owner):
            self.calls += 1

    observer = Recorder()
    calculator.add_observer(observer)
    with pytest.raises(ValidationError, match="magnitude"):
        calculator.calculate("add", outside, 0)
    assert calculator.history == before
    assert observer.calls == 0
    calculator.redo()
    assert [item.result for item in calculator.history] == [3, 7]


def test_invalid_and_nonfinite_inputs_still_fail_under_limit(tmp_path):
    calculator = Calculator(config=configured(tmp_path))
    with pytest.raises(ValidationError):
        calculator.calculate("add", float("nan"), 2)
    with pytest.raises(ValidationError):
        calculator.calculate("add", "bad", 2)
    assert calculator.history == ()


def test_precision_agrees_across_result_history_log_and_csv(tmp_path):
    config = configured(tmp_path, CALCULATOR_PRECISION="2", CALCULATOR_AUTO_SAVE="true")
    calculator = Calculator(config=config)
    result = calculator.calculate("divide", 1, 8)
    assert result == 0.12
    assert calculator.history[0].result == result
    assert "Calculated divide(1.0, 8.0) = 0.12" in config.log_file.read_text(encoding="utf-8")
    restored = Calculator()
    restored.load_history(config.history_file)
    assert restored.history == calculator.history
    assert "0.12" in config.history_file.read_text(encoding="utf-8")


def test_integer_division_keeps_integer_result_with_precision(tmp_path):
    calculator = Calculator(config=configured(tmp_path, CALCULATOR_PRECISION="0"))
    assert calculator.calculate("int_divide", -7, 2) == -3
    assert type(calculator.history[0].result) is int


def test_configured_paths_and_encoding_reach_existing_components(tmp_path):
    config = configured(
        tmp_path, CALCULATOR_LOG_DIR="custom-logs", CALCULATOR_HISTORY_DIR="custom-data",
        CALCULATOR_DEFAULT_ENCODING="utf-16", CALCULATOR_AUTO_SAVE="true",
    )
    calculator = Calculator(config=config)
    calculator.calculate("add", 2, 3)
    assert "Calculated add" in config.log_file.read_text(encoding="utf-16")
    loaded = Calculator(config=config, auto_save=False)
    loaded.load_history()
    assert loaded.history == calculator.history
    loaded.clear_history()
    loaded.save_history()
    loaded.load_history()
    assert loaded.history == ()


def test_explicit_constructor_values_override_configured_files_and_auto_save(tmp_path):
    config = configured(tmp_path, CALCULATOR_AUTO_SAVE="true")
    alternate_log = tmp_path / "alternate.log"
    alternate_history = tmp_path / "alternate.csv"
    calculator = Calculator(
        config=config, log_file=alternate_log, history_file=alternate_history, auto_save=False,
    )
    calculator.calculate("add", 2, 3)
    assert alternate_log.exists()
    assert not config.log_file.exists()
    assert not alternate_history.exists()
    assert not config.history_file.exists()
    calculator.save_history()
    assert alternate_history.exists()


def test_missing_manual_history_path_has_clear_error():
    calculator = Calculator()
    with pytest.raises(ConfigurationError, match="history file path"):
        calculator.save_history()
    with pytest.raises(ConfigurationError, match="history file path"):
        calculator.load_history()


def test_history_limit_keeps_newest_and_undo_redo_restore_bounded_snapshots(tmp_path):
    calculator = Calculator(config=configured(tmp_path, CALCULATOR_MAX_HISTORY_SIZE="2"))
    calculator.calculate("add", 1, 1)
    calculator.calculate("add", 2, 1)
    before = calculator.history
    calculator.calculate("add", 3, 1)
    after = calculator.history
    assert [entry.result for entry in after] == [3, 4]
    calculator.undo()
    assert calculator.history == before
    calculator.redo()
    assert calculator.history == after
    calculator.undo()
    calculator.calculate("subtract", 8, 1)
    assert [entry.result for entry in calculator.history] == [3, 7]
    with pytest.raises(OperationError, match="Nothing to redo"):
        calculator.redo()


def test_failed_calculation_does_not_trim_full_history_or_change_redo(tmp_path):
    calculator = Calculator(config=configured(tmp_path, CALCULATOR_MAX_HISTORY_SIZE="2"))
    for value in (1, 2, 3):
        calculator.calculate("add", value, 1)
    calculator.undo()
    before = calculator.history
    with pytest.raises(OperationError):
        calculator.calculate("divide", 1, 0)
    assert calculator.history == before
    calculator.redo()
    assert [entry.result for entry in calculator.history] == [3, 4]


def test_loading_validates_all_rows_before_applying_history_limit(tmp_path):
    source = Calculator()
    for value in (1, 2, 3):
        source.calculate("add", value, 1)
    path = tmp_path / "incoming.csv"
    source.save_history(path)
    target = Calculator(config=configured(tmp_path, CALCULATOR_MAX_HISTORY_SIZE="2"))
    target.calculate("multiply", 2, 3)
    target.load_history(path)
    assert target.history == source.history[1:]
    with pytest.raises(OperationError, match="Nothing to undo"):
        target.undo()

    content = path.read_text(encoding="utf-8").replace("add,1.0", "unknown,1.0", 1)
    path.write_text(content, encoding="utf-8")
    before = target.history
    with pytest.raises(PersistenceError, match="row 2"):
        target.load_history(path)
    assert target.history == before
    with pytest.raises(OperationError, match="Nothing to undo"):
        target.undo()
