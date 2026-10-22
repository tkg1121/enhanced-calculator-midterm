"""Arithmetic operations for two numeric operands."""

from typing import Protocol

from app.exceptions import OperationError


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


class Operation(Protocol):
    """Common interface for operations created by the factory."""

    def execute(self, first: float, second: float) -> float: ...


class AddOperation:
    def execute(self, first: float, second: float) -> float:
        return add(first, second)


class SubtractOperation:
    def execute(self, first: float, second: float) -> float:
        return subtract(first, second)


class MultiplyOperation:
    def execute(self, first: float, second: float) -> float:
        return multiply(first, second)


class DivideOperation:
    def execute(self, first: float, second: float) -> float:
        return divide(first, second)


class OperationFactory:
    """Create an operation object from its user-facing name."""

    _operations: dict[str, type[Operation]] = {
        "add": AddOperation,
        "subtract": SubtractOperation,
        "multiply": MultiplyOperation,
        "divide": DivideOperation,
    }

    @classmethod
    def create(cls, name: str) -> Operation:
        if not isinstance(name, str):
            raise OperationError("Operation name must be text.")
        try:
            return cls._operations[name.strip().lower()]()
        except KeyError as error:
            choices = ", ".join(cls._operations)
            raise OperationError(f"Unknown operation. Choose: {choices}.") from error
