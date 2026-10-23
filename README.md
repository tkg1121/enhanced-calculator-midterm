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
history unchanged. `history` returns an immutable tuple of records, and
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

## Testing

```powershell
python -m pytest
python -m pytest --cov=app --cov-report=term-missing
```
