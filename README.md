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
and root.
Each operation takes two numeric operands. `OperationFactory.create()` selects
an operation by name, ignoring surrounding spaces and letter case. Unsupported
names raise `OperationError`. Division by zero raises a `ZeroDivisionError`.

`power(a, b)` raises `a` to `b`. A negative base requires an integer exponent;
`power(0, 0)` returns 1. `root(a, b)` calculates the `b`-th root of `a`.
Negative radicands require odd integer degrees. A zero degree, a negative
degree applied to zero, complex-valued results, and overflow are rejected.

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

## Testing

```powershell
python -m pytest
```
