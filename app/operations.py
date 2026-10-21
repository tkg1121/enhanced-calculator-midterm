"""Arithmetic operations for two numeric operands."""


def add(first: float, second: float) -> float:
    """Return the sum of the operands."""
    return first + second


def subtract(first: float, second: float) -> float:
    """Return the first operand minus the second."""
    return first - second


def multiply(first: float, second: float) -> float:
    """Return the product of the operands."""
    return first * second


def divide(first: float, second: float) -> float:
    """Return the quotient, rejecting a zero divisor."""
    if second == 0:
        raise ZeroDivisionError("Cannot divide by zero.")
    return first / second
