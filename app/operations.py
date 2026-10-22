"""Arithmetic operations for two numeric operands."""

import math
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


def power(first: float, second: float) -> float:
    """Raise the first operand to the second within the real-number domain."""
    if first < 0 and not float(second).is_integer():
        raise OperationError("A negative base requires an integer exponent.")
    if first == 0 and second < 0:
        raise OperationError("Zero cannot be raised to a negative exponent.")
    try:
        result = math.pow(first, second)
    except (ValueError, OverflowError) as error:
        raise OperationError("Power result is undefined or too large.") from error
    if not math.isfinite(result):
        raise OperationError("Power result must be finite.")
    return result


def root(first: float, second: float) -> float:
    """Return the second operand's root of the first, when real-valued."""
    if second == 0:
        raise OperationError("Root degree cannot be zero.")
    if first == 0 and second < 0:
        raise OperationError("Zero cannot have a negative root degree.")
    if first < 0:
        degree = float(second)
        if not degree.is_integer() or int(degree) % 2 == 0:
            raise OperationError("A negative radicand requires an odd integer degree.")
        return -power(-first, 1 / degree)
    return power(first, 1 / second)


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


class PowerOperation:
    def execute(self, first: float, second: float) -> float:
        return power(first, second)


class RootOperation:
    def execute(self, first: float, second: float) -> float:
        return root(first, second)


class OperationFactory:
    """Create an operation object from its user-facing name."""

    _operations: dict[str, type[Operation]] = {
        "add": AddOperation,
        "subtract": SubtractOperation,
        "multiply": MultiplyOperation,
        "divide": DivideOperation,
        "power": PowerOperation,
        "root": RootOperation,
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
