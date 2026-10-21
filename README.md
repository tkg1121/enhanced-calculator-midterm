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

The calculator currently supports addition and subtraction. Each operation
takes two numeric operands.

## Usage

```python
from app.operations import add, subtract

print(add(2, 3))       # 5
print(subtract(5, 2))  # 3
```

## Testing

```powershell
python -m pytest
```
