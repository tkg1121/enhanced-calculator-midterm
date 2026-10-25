"""Plain-text command loop for the calculator's existing programmatic API."""

import sys
import warnings
from collections.abc import Callable

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
) -> None:
    """Read commands until exit, EOF, or Ctrl+C."""
    output("Calculator ready. Type help for commands.")
    while True:
        try:
            line = input_func("calc> ")
        except (EOFError, KeyboardInterrupt):
            output("Goodbye.")
            return
        if not execute_command(line, calculator, output):
            return


def main(
    *,
    config: CalculatorConfig | None = None,
    input_func: Callable[[str], str] = input,
    output: Callable[[str], None] = print,
) -> int:
    """Start the configured calculator or report a startup error."""
    try:
        calculator = Calculator(config=config if config is not None else CalculatorConfig.load())
    except (ConfigurationError, OSError, LookupError) as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 2
    run_repl(calculator, input_func, output)
    return 0
