"""Command parsing, recovery, and the executable entry point."""

import os
import subprocess
import sys

import pytest

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig, DEFAULTS
from app.exceptions import ConfigurationError, OperationError, PersistenceError
from app.repl import execute_command, main, run_repl


def configured(tmp_path, **overrides):
    return CalculatorConfig.load(base_dir=tmp_path, environ={}, overrides=overrides)


def run_lines(calculator, lines):
    output = []
    commands = iter(lines)
    run_repl(calculator, lambda prompt: next(commands), output.append)
    return output


@pytest.mark.parametrize(
    "command,expected",
    [
        ("add 2 3", 5),
        ("subtract 8 3", 5),
        ("multiply 3 4", 12),
        ("divide 9 2", 4.5),
        ("power 2 3", 8),
        ("root 27 3", 3),
        ("modulus 7 3", 1),
        ("int_divide -7 2", -3),
        ("percent 1 4", 25),
        ("abs_diff 2 5", 3),
    ],
)
def test_all_arithmetic_commands_use_calculator(command, expected):
    calculator = Calculator()
    output = []
    assert execute_command(command, calculator, output.append) is True
    assert calculator.history[0].result == pytest.approx(expected)
    assert output == [f"Result: {calculator.history[0].result}"]


def test_scripted_sequence_saves_clears_loads_and_exits(tmp_path):
    calculator = Calculator(config=configured(tmp_path))
    output = run_lines(calculator, [
        "add 2 3", "multiply 4 5", "undo", "redo", "history", "save",
        "clear", "history", "load", "history", "exit",
    ])
    assert [entry.result for entry in calculator.history] == [5, 20]
    assert "History saved." in output
    assert "History cleared." in output
    assert "History loaded." in output
    assert "History is empty." in output
    assert sum("multiply(4.0, 5.0) = 20.0" in line for line in output) == 2
    assert output[-1] == "Goodbye."
    assert calculator.history[1].timestamp.isoformat() in output[-2]
    with pytest.raises(OperationError, match="Nothing to undo"):
        calculator.undo()


def test_recoverable_errors_followed_by_success():
    calculator = Calculator()
    output = run_lines(calculator, [
        "", "mystery", "add 1", "add 1 2 3", "divide 1 0", "add bad 2",
        "undo", "redo", "history", "clear", "clear", "add 2 3", "exit",
    ])
    assert any("Unknown command" in line for line in output)
    assert output.count("Usage: add <first_operand> <second_operand>") == 2
    assert any("Cannot divide by zero" in line for line in output)
    assert any("Enter a real number" in line for line in output)
    assert any("Nothing to undo" in line for line in output)
    assert any("Nothing to redo" in line for line in output)
    assert "History is empty." in output
    assert "History is already empty." in output
    assert "Result: 5.0" in output
    assert [entry.result for entry in calculator.history] == [5]


def test_help_and_control_command_argument_counts():
    output = []
    calculator = Calculator()
    execute_command("help", calculator, output.append)
    execute_command("save extra", calculator, output.append)
    execute_command("history extra", calculator, output.append)
    execute_command("exit extra", calculator, output.append)
    assert "int_divide" in output[0] and "<operation>" in output[0]
    assert output[1:] == ["Usage: save", "Usage: history", "Usage: exit"]


def test_save_and_load_errors_are_recoverable():
    output = run_lines(Calculator(), ["save", "load", "add 2 3", "exit"])
    assert sum("history file path is required" in line for line in output) == 2
    assert "Result: 5.0" in output


def test_missing_configured_csv_reports_error_then_accepts_next_command(tmp_path):
    output = run_lines(Calculator(config=configured(tmp_path)), ["load", "add 2 3", "exit"])
    assert any("Could not load history" in line for line in output)
    assert "Result: 5.0" in output


def test_auto_save_failure_is_shown_without_losing_result(tmp_path, monkeypatch):
    calculator = Calculator(config=configured(tmp_path, CALCULATOR_AUTO_SAVE="true"))

    def fail_save(*args, **kwargs):
        raise PersistenceError("simulated disk error")

    monkeypatch.setattr("app.calculator.save_history", fail_save)
    output = run_lines(calculator, ["add 2 3", "exit"])
    assert "Result: 5.0" in output
    assert any("Warning:" in line and "simulated disk error" in line for line in output)
    assert len(calculator.history) == 1


@pytest.mark.parametrize("error", [EOFError, KeyboardInterrupt])
def test_prompt_eof_and_ctrl_c_exit_cleanly(error):
    output = []

    def interrupt(prompt):
        raise error

    run_repl(Calculator(), interrupt, output.append)
    assert output[-1] == "Goodbye."


def test_invalid_startup_configuration_returns_nonzero(tmp_path, monkeypatch, capsys):
    def fail_load(cls):
        raise ConfigurationError("invalid precision")

    monkeypatch.setattr(CalculatorConfig, "load", classmethod(fail_load))
    assert main(input_func=lambda prompt: "exit") == 2
    assert "Configuration error: invalid precision" in capsys.readouterr().err


def test_module_entry_point_runs_with_isolated_paths(tmp_path):
    env = os.environ.copy()
    env.update(DEFAULTS)
    env["CALCULATOR_LOG_DIR"] = str(tmp_path / "logs")
    env["CALCULATOR_HISTORY_DIR"] = str(tmp_path / "data")
    completed = subprocess.run(
        [sys.executable, "-m", "app"], input="add 2 3\nexit\n", text=True,
        capture_output=True, env=env, check=False,
    )
    assert completed.returncode == 0
    assert "Result: 5.0" in completed.stdout
    assert "Goodbye." in completed.stdout
    assert (tmp_path / "logs" / "calculator.log").exists()
    assert not (tmp_path / "data" / "history.csv").exists()


def test_startup_does_not_replace_existing_history_file(tmp_path):
    config = configured(tmp_path, CALCULATOR_AUTO_SAVE="true")
    config.history_file.write_bytes(b"existing history bytes")
    output = []
    assert main(config=config, input_func=lambda prompt: "exit", output=output.append) == 0
    assert config.history_file.read_bytes() == b"existing history bytes"


def test_module_entry_point_rejects_invalid_configuration(tmp_path):
    env = os.environ.copy()
    env.update(DEFAULTS)
    env["CALCULATOR_LOG_DIR"] = str(tmp_path / "logs")
    env["CALCULATOR_HISTORY_DIR"] = str(tmp_path / "data")
    env["CALCULATOR_PRECISION"] = "invalid"
    completed = subprocess.run(
        [sys.executable, "-m", "app"], input="", text=True,
        capture_output=True, env=env, check=False,
    )
    assert completed.returncode != 0
    assert "Configuration error" in completed.stderr
    assert "CALCULATOR_PRECISION" in completed.stderr
