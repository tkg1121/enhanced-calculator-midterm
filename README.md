# Enhanced Calculator Midterm

A Python calculator with two-operand arithmetic operations.

## Installation

Use Python 3.12 or newer. From the project directory, create a virtual
environment and install the dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

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
`OperationError`. All operations use finite real numbers; no input-size limit
is currently configured.

`power(a, b)` raises `a` to `b`. A negative base requires an integer exponent;
`power(0, 0)` returns 1. `root(a, b)` calculates the `b`-th root of `a`.
Negative radicands require odd integer degrees. A zero degree, a negative
degree applied to zero, complex-valued results, and overflow are rejected.
`modulus(a, b)` follows Python's `%` remainder rule, so the result takes the
divisor's sign. `int_divide(a, b)` truncates the quotient toward zero, making
`int_divide(-7, 2)` return `-3`. `percent(a, b)` returns `(a / b) * 100`.

## Usage

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

## Testing

```powershell
python -m pytest
python -m pytest --cov=app --cov-report=term-missing
```
