# Enhanced Calculator Midterm

A command-line Python calculator with ten two-operand operations, calculation
history, undo/redo, file logging, optional automatic CSV saving, and
color-coded interactive output. Settings come from `.env`, and the test suite
runs in GitHub Actions.

## Installation

Python 3.12 is used by the CI workflow. From the project directory, create a
virtual environment and install the dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, use `python3.12 -m venv .venv`,
`source .venv/bin/activate`, and the same `python -m pip install` command.

Copy `.env.example` to `.env` for local settings:

```powershell
Copy-Item .env.example .env
```

The local `.env` is ignored by Git. `CalculatorConfig.load()` reads settings
when called; importing modules does not load configuration or create files.
Process environment variables override `.env`, explicit `overrides` override
both, and absent settings use the defaults in `.env.example`. Invalid supplied
values raise `ConfigurationError`.

Relative log and history directories resolve from the project root. Relative
log and history file names resolve under their respective directories;
absolute file paths are used directly. Loading configuration creates missing
directories but does not create log or history files.

| Setting | Default | Rule |
| --- | --- | --- |
| `CALCULATOR_LOG_DIR` | `logs` | Nonempty directory path |
| `CALCULATOR_HISTORY_DIR` | `data` | Nonempty directory path |
| `CALCULATOR_MAX_HISTORY_SIZE` | `1000` | Positive integer |
| `CALCULATOR_AUTO_SAVE` | `false` | `true` or `false`, case insensitive |
| `CALCULATOR_PRECISION` | `15` | Nonnegative integer decimal places |
| `CALCULATOR_MAX_INPUT_VALUE` | `1e308` | Positive finite number |
| `CALCULATOR_DEFAULT_ENCODING` | `utf-8` | Recognized text encoding |
| `CALCULATOR_LOG_FILE` | `calculator.log` | Nonempty file path under log directory if relative |
| `CALCULATOR_HISTORY_FILE` | `history.csv` | Nonempty file path under history directory if relative |

Pass the loaded configuration to `Calculator` to apply it in programmatic use:

```python
from app.calculator_config import CalculatorConfig
from app.calculator import Calculator

calculator = Calculator(config=CalculatorConfig.load())
```

The maximum input setting limits the absolute magnitude of each operand;
values exactly at the limit are accepted. Precision means decimal places on
floating-point results and uses Python's `round` policy (ties to even for
representable halfway values). Integer division stays an integer and still
truncates toward zero. Returned results, history entries, logs, and CSV files
use the rounded result. Loaded or restored records keep their saved results
and timestamps. A plain `Calculator()` keeps its original unconfigured
programmatic behavior. `CALCULATOR_MAX_HISTORY_SIZE` keeps the newest
calculation entries when the current history exceeds its limit. Undo restores
the bounded state from before the latest action; the setting does not limit
the undo and redo stacks. Loading validates the entire CSV before keeping its
newest entries and starting a new undo/redo baseline.

## Supported functionality

The calculator supports addition, subtraction, multiplication, division, power,
root, modulus, integer division (`int_divide`), percentage (`percent`), and
absolute difference (`abs_diff`).
The `Calculator` class returns each numeric result and keeps completed
calculations in chronological, in-memory history. Failed calculations leave
history unchanged. Each record has a timezone-aware UTC creation timestamp.
`history` returns an immutable tuple of records, and
`clear_history()` removes the current records. A nonempty clear can be undone
or redone; clearing empty history has no effect on undo or redo.
Each operation takes two numeric operands. `OperationFactory.create()` selects
an operation by name, ignoring surrounding spaces and letter case. Unsupported
names and zero denominators raise `OperationError`. Numeric strings such as
`"2.5"` are accepted. Booleans, nonnumeric values, NaN, and infinity raise
`ValidationError`. Results that overflow or are nonfinite raise
`OperationError`. All operations use finite real numbers; input limits apply
when a configuration is supplied.

`power(a, b)` raises `a` to `b`. A negative base requires an integer exponent;
`power(0, 0)` returns 1. `root(a, b)` calculates the `b`-th root of `a`.
Negative radicands require odd integer degrees. A zero degree, a negative
degree applied to zero, complex-valued results, and overflow are rejected.
`modulus(a, b)` follows Python's `%` remainder rule, so the result takes the
divisor's sign. `int_divide(a, b)` truncates the quotient toward zero, making
`int_divide(-7, 2)` return `-3`. `percent(a, b)` returns `(a / b) * 100`.

## Usage

Run the interactive calculator from the project directory:

```powershell
python -m app
```

Enter `<operation> <first_operand> <second_operand>`. The available operations
are `add`, `subtract`, `multiply`, `divide`, `power`, `root`, `modulus`,
`int_divide`, `percent`, and `abs_diff`. The other commands are `history`,
`clear`, `undo`, `redo`, `save`, `load`, `help`, and `exit`. For example:

```text
calc> add 2 3
Result: 5.0
calc> history
1. 2026-10-25T12:00:00+00:00 add(2.0, 3.0) = 5.0
calc> undo
Undone.
calc> redo
Redone.
calc> save
History saved.
calc> exit
Goodbye.
```

The history line's timestamp reflects the actual calculation time. `save` and
`load` use the configured CSV path; neither takes a filename argument. Blank
lines are ignored. Unknown commands, incorrect operand counts, invalid
numbers, and unavailable undo/redo report errors and leave the loop running.
EOF and Ctrl+C at the prompt exit cleanly. Invalid startup settings print a
configuration error and exit with a nonzero status. Starting the application
does not automatically load history or write a history CSV.

Interactive terminal output uses Colorama: results are green, errors are red,
warnings and usage hints are yellow, and help headings are cyan. Every message
retains its text label and resets styling. Redirected output and noninteractive
runs are plain by default. Programmatic callers of `run_repl()` or `main()` can
pass `color=True` or `color=False` to make the choice explicit. Color codes are
never stored in calculation records, CSV history, or log files.

The operations are also available in Python code:

```python
from app.operations import OperationFactory, add, divide, multiply, power, root, subtract

print(add(2, 3))       # 5
print(subtract(5, 2))  # 3
print(multiply(4, 3))  # 12
print(divide(9, 2))    # 4.5
print(OperationFactory.create("add").execute(2, 3))  # 5
print(power(2, -2))    # 0.25
print(root(-27, 3))    # approximately -3
```

To keep a calculation history:

```python
from app.calculator import Calculator

calculator = Calculator()
print(calculator.calculate("add", 2, 3))
print(calculator.history)
calculator.undo()
calculator.redo()
calculator.clear_history()
```

`calculator.undo()` restores history before the latest successful calculation
or nonempty clear. `calculator.redo()` restores the undone state. Multiple undo
and redo steps are supported. A new successful calculation or nonempty clear
after undo discards the previous redo branch. A failed calculation leaves the
history and undo/redo state unchanged. Calling undo or redo with no available
state raises `OperationError` with a `Nothing to undo` or `Nothing to redo`
message. Restoring history does not perform arithmetic again.

## CSV history

Install pandas through `requirements.txt`. Save or load history with an explicit
path; UTF-8 is the default encoding and both methods accept an `encoding`
argument:

```python
calculator.save_history("data/history.csv")
calculator.load_history("data/history.csv")
```

The CSV columns are `operation,first,second,result,timestamp`. Timestamps use
ISO 8601 with a UTC offset. An empty history saves as a header-only CSV. Saving
creates missing parent directories and replaces an existing file only after a
complete write. A successful load validates all rows, replaces the current
history, and clears the old undo and redo stacks. A failed load leaves those
states unchanged. Loading does not run calculations again. Manual save writes
the current state, including after undo, redo, or clear. File and record errors
raise `PersistenceError`.

## Logging and observers

Pass `log_file` to `Calculator` to log completed calculations and history
save/load events to that path. No log file is created by the default
constructor. The optional `encoding` argument controls log text encoding;
UTF-8 is the default.

```python
calculator = Calculator(log_file="logs/calculator.log")
calculator.calculate("add", 2, 3)
```

Observers implement `on_calculation(record, calculator)` and can be registered
with `add_observer()` or removed with `remove_observer()`. The same object is
registered at most once. Observers run after each successful calculation is
recorded and after undo/redo state is updated. Failed calculations, undo, redo,
clear, and load do not send calculation notifications. A file-I/O failure from
an observer emits a warning, allows the other observers to run, and does not
remove the successful calculation. Unrelated programming errors still raise.

## Automatic saving

Set `history_file` and `auto_save=True` to save the complete current history
after every successful new calculation. The default is `auto_save=False`, so
the constructor does not write a history file unless enabled. Both logging and
CSV use the constructor's `encoding` value, which defaults to UTF-8. Manual
save/load can override it with their own `encoding` argument.

```python
calculator = Calculator(
    log_file="logs/calculator.log",
    history_file="data/history.csv",
    auto_save=True,
)
calculator.calculate("add", 2, 3)
```

Auto-save uses the same atomic CSV writer as manual save. It runs only for new
successful calculations; undo, redo, clear, and load leave the last saved file
alone until another calculation or manual save. If auto-save fails, the
calculation remains in history, other observers still run, and a warning is
emitted. Passing `auto_save=True` without `history_file` raises `ValueError`.

## Design patterns

`OperationFactory` in `app/operations.py` creates the requested arithmetic
operation. `CalculatorMemento` and `UndoRedo` in `app/calculator_memento.py`
hold history snapshots for undo and redo. `Calculator` registers and notifies
`LoggingObserver` and `AutoSaveObserver` in `app/observers.py` after each
successful calculation. Terminal colors are applied only in `app/repl.py`.

## Testing

```powershell
python -m pytest
python -m pytest --cov=app --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=90
```

The second command measures statement and branch coverage across `app/` and
fails below 90% total coverage. It writes `coverage.xml`, which is ignored by
Git. The GitHub Actions workflow runs the same command on pushes to `main` and
pull requests targeting `main`, using Python 3.12 after installing
`requirements.txt`. A failing test or coverage below 90% fails the workflow.
