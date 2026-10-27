"""Terminal styling stays in the command interface and out of saved data."""

import io
from contextlib import redirect_stdout

from colorama import Fore, Style

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app.exceptions import ConfigurationError
from app.repl import main, run_repl


class TerminalBuffer(io.StringIO):
    def __init__(self, interactive):
        super().__init__()
        self.interactive = interactive

    def isatty(self):
        return self.interactive


def scripted(calculator, commands, *, color=None, output=None):
    lines = iter(commands)
    messages = [] if output is None else output
    run_repl(calculator, lambda prompt: next(lines), messages.append, color=color)
    return messages


def test_colored_results_errors_warnings_and_help_reset_styling():
    messages = scripted(Calculator(), ["help", "add 1", "mystery", "divide 1 0", "add 2 3", "history", "exit"], color=True)
    help_text = messages[1]
    assert f"{Fore.CYAN}Operations:{Style.RESET_ALL}" in help_text
    assert f"{Fore.CYAN}Commands:{Style.RESET_ALL}" in help_text
    assert "int_divide" in help_text and "<operation>" in help_text
    assert messages[2] == f"{Fore.YELLOW}Usage: add <first_operand> <second_operand>{Style.RESET_ALL}"
    assert messages[3].startswith(f"{Fore.RED}Unknown command:")
    assert messages[3].endswith(Style.RESET_ALL)
    assert messages[4].startswith(f"{Fore.RED}Error: Cannot divide by zero.")
    assert messages[4].endswith(Style.RESET_ALL)
    assert messages[5] == f"{Fore.GREEN}Result: 5.0{Style.RESET_ALL}"
    assert "add(2.0, 3.0) = 5.0" in messages[6]
    assert messages[-1] == "Goodbye."


def test_explicit_plain_output_remains_readable():
    messages = scripted(Calculator(), ["help", "add 1", "mystery", "add 2 3", "exit"], color=False)
    assert "Operations:" in messages[1] and "Commands:" in messages[1]
    assert messages[2] == "Usage: add <first_operand> <second_operand>"
    assert messages[3].startswith("Unknown command:")
    assert messages[4] == "Result: 5.0"
    assert all("\x1b[" not in message for message in messages)


def test_noninteractive_standard_output_is_plain_by_default():
    stream = TerminalBuffer(interactive=False)
    commands = iter(["help", "add 2 3", "exit"])
    with redirect_stdout(stream):
        run_repl(Calculator(), lambda prompt: next(commands))
    assert "Calculator ready." in stream.getvalue()
    assert "Operations:" in stream.getvalue()
    assert "Result: 5.0" in stream.getvalue()
    assert "\x1b[" not in stream.getvalue()


def test_interactive_detection_can_be_controlled_without_a_real_terminal(monkeypatch):
    monkeypatch.setattr("app.repl.just_fix_windows_console", lambda: None)
    stream = TerminalBuffer(interactive=True)
    commands = iter(["add 2 3", "exit"])
    with redirect_stdout(stream):
        run_repl(Calculator(), lambda prompt: next(commands))
    assert f"{Fore.GREEN}Result: 5.0{Style.RESET_ALL}" in stream.getvalue()


def test_colored_repl_recovers_and_keeps_logs_and_csv_plain(tmp_path):
    config = CalculatorConfig.load(
        base_dir=tmp_path, environ={}, overrides={"CALCULATOR_AUTO_SAVE": "true"},
    )
    calculator = Calculator(config=config)
    messages = scripted(calculator, ["divide 1 0", "add 2 3", "exit"], color=True)
    assert messages[1].startswith(f"{Fore.RED}Error:")
    assert messages[2] == f"{Fore.GREEN}Result: 5.0{Style.RESET_ALL}"
    assert [(entry.operation, entry.result) for entry in calculator.history] == [("add", 5.0)]
    assert "\x1b[" not in config.log_file.read_text(encoding=config.encoding)
    assert "\x1b[" not in config.history_file.read_text(encoding=config.encoding)


def test_colored_observer_warning_still_follows_successful_result(tmp_path, monkeypatch):
    config = CalculatorConfig.load(
        base_dir=tmp_path, environ={}, overrides={"CALCULATOR_AUTO_SAVE": "true"},
    )
    calculator = Calculator(config=config)

    def fail_save(*args, **kwargs):
        from app.exceptions import PersistenceError
        raise PersistenceError("disk unavailable")

    monkeypatch.setattr("app.calculator.save_history", fail_save)
    messages = scripted(calculator, ["add 2 3", "exit"], color=True)
    assert messages[1] == f"{Fore.GREEN}Result: 5.0{Style.RESET_ALL}"
    assert messages[2].startswith(f"{Fore.YELLOW}Warning:")
    assert messages[2].endswith(Style.RESET_ALL)
    assert "disk unavailable" in messages[2]


def test_startup_error_respects_explicit_color_choice(monkeypatch, capsys):
    def fail_load(cls):
        raise ConfigurationError("invalid precision")

    monkeypatch.setattr(CalculatorConfig, "load", classmethod(fail_load))
    monkeypatch.setattr("app.repl.just_fix_windows_console", lambda: None)
    assert main(color=True) == 2
    assert capsys.readouterr().err == (
        f"{Fore.RED}Configuration error: invalid precision{Style.RESET_ALL}\n"
    )
    assert main(color=False) == 2
    assert capsys.readouterr().err == "Configuration error: invalid precision\n"
