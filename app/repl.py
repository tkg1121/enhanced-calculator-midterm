"""Command loop and terminal presentation for the calculator."""

import sys
import warnings
from collections.abc import Callable

from colorama import Fore, Style, just_fix_windows_console

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app.exceptions import CalculatorError, ConfigurationError


OPERATIONS = (
    "add", "subtract", "multiply", "divide", "power", "root", "modulus",
    "int_divide", "percent", "abs_diff",
)
HELP = (
    "Enter <operation> <first_operand> <second_operand>.\n"
    f"Operations: {', '.join(OPERATIONS)}.\n"
    "Commands: history, clear, undo, redo, save, load, help, exit."
)


def _use_color(color: bool | None, output: Callable[[str], None]) -> bool:
    """Use color automatically only for the standard interactive output."""
    return color if color is not None else output is print and sys.stdout.isatty()


def _format_message(message: str, color: bool) -> str:
    """Add terminal styling without changing the readable message text."""
    if not color:
        return message
    if message.startswith("Result:"):
        return f"{Fore.GREEN}{message}{Style.RESET_ALL}"
    if message.startswith(("Error:", "Configuration error:", "Unknown command:")):
        return f"{Fore.RED}{message}{Style.RESET_ALL}"
    if message.startswith(("Warning:", "Usage:", "History is empty.", "History is already empty.")):
        return f"{Fore.YELLOW}{message}{Style.RESET_ALL}"
    if message == HELP:
        return message.replace("Operations:", f"{Fore.CYAN}Operations:{Style.RESET_ALL}").replace(
            "Commands:", f"{Fore.CYAN}Commands:{Style.RESET_ALL}"
        )
    return message


def execute_command(line: str, calculator: Calculator, output: Callable[[str], None]) -> bool:
    """Run one command; return False only when the user requests exit."""
    parts = line.split()
    if not parts:
        return True
    command = parts[0].lower()
    if command in OPERATIONS:
        if len(parts) != 3:
            output(f"Usage: {command} <first_operand> <second_operand>")
            return True
        with warnings.catch_warnings(record=True) as notices:
            warnings.simplefilter("always", RuntimeWarning)
            try:
                result = calculator.calculate(command, parts[1], parts[2])
            except CalculatorError as error:
                output(f"Error: {error}")
                return True
        output(f"Result: {result}")
        for notice in notices:
            output(f"Warning: {notice.message}")
        return True
    if command not in {"history", "clear", "undo", "redo", "save", "load", "help", "exit"}:
        output(f"Unknown command: {parts[0]}. Type help for available commands.")
        return True
    if len(parts) != 1:
        output(f"Usage: {command}")
        return True
    if command == "exit":
        output("Goodbye.")
        return False
    if command == "help":
        output(HELP)
        return True
    try:
        if command == "history":
            if not calculator.history:
                output("History is empty.")
            else:
                for index, record in enumerate(calculator.history, start=1):
                    output(
                        f"{index}. {record.timestamp.isoformat()} "
                        f"{record.operation}({record.first}, {record.second}) = {record.result}"
                    )
        elif command == "clear":
            if calculator.history:
                calculator.clear_history()
                output("History cleared.")
            else:
                output("History is already empty.")
        elif command == "undo":
            calculator.undo()
            output("Undone.")
        elif command == "redo":
            calculator.redo()
            output("Redone.")
        elif command == "save":
            calculator.save_history()
            output("History saved.")
        elif command == "load":
            calculator.load_history()
            output("History loaded.")
    except CalculatorError as error:
        output(f"Error: {error}")
    return True


def run_repl(
    calculator: Calculator,
    input_func: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
    *,
    color: bool | None = None,
) -> None:
    """Read commands until exit, EOF, or Ctrl+C."""
    enabled = _use_color(color, output)
    if enabled and output is print:
        just_fix_windows_console()

    def emit(message: str) -> None:
        output(_format_message(message, enabled))

    emit("Calculator ready. Type help for commands.")
    while True:
        try:
            line = input_func("calc> ")
        except (EOFError, KeyboardInterrupt):
            emit("Goodbye.")
            return
        if not execute_command(line, calculator, emit):
            return


def main(
    *,
    config: CalculatorConfig | None = None,
    input_func: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
    color: bool | None = None,
) -> int:
    """Start the configured calculator or report a startup error."""
    try:
        calculator = Calculator(config=config if config is not None else CalculatorConfig.load())
    except (ConfigurationError, OSError, LookupError) as error:
        enabled = color if color is not None else sys.stdout.isatty() and sys.stderr.isatty()
        if enabled:
            just_fix_windows_console()
        print(_format_message(f"Configuration error: {error}", enabled), file=sys.stderr)
        return 2
    run_repl(calculator, input_func, output, color=color)
    return 0
