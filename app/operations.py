"""Arithmetic operations for two numeric operands."""

import math
from typing import Protocol

from app.exceptions import OperationError
from app.input_validators import validate_operands


def _finite_result(result: float) -> float:
    if not math.isfinite(result):
        raise OperationError("Result is too large for a finite real number.")
    return result


def add(first: float, second: float) -> float:
    """Return the sum of the operands."""
    first, second = validate_operands(first, second)
    return _finite_result(first + second)


def subtract(first: float, second: float) -> float:
    """Return the first operand minus the second."""
    first, second = validate_operands(first, second)
    return _finite_result(first - second)


def multiply(first: float, second: float) -> float:
    """Return the product of the operands."""
    first, second = validate_operands(first, second)
    return _finite_result(first * second)


def divide(first: float, second: float) -> float:
    """Return the quotient, rejecting a zero divisor."""
    first, second = validate_operands(first, second)
    if second == 0:
        raise OperationError("Cannot divide by zero.")
    return _finite_result(first / second)


def power(first: float, second: float) -> float:
    """Raise the first operand to the second within the real-number domain."""
    first, second = validate_operands(first, second)
    if first < 0 and not second.is_integer():
        raise OperationError("A negative base requires an integer exponent.")
    if first == 0 and second < 0:
        raise OperationError("Zero cannot be raised to a negative exponent.")
    try:
        result = math.pow(first, second)
    except (ValueError, OverflowError) as error:
        raise OperationError("Power result is undefined or too large.") from error
    return _finite_result(result)


def root(first: float, second: float) -> float:
    """Return the second operand's root of the first, when real-valued."""
    first, second = validate_operands(first, second)
    if second == 0:
        raise OperationError("Root degree cannot be zero.")
    if first == 0 and second < 0:
        raise OperationError("Zero cannot have a negative root degree.")
    if first < 0:
        if not second.is_integer() or int(second) % 2 == 0:
            raise OperationError("A negative radicand requires an odd integer degree.")
        return -power(-first, _finite_result(1 / second))
    return power(first, _finite_result(1 / second))


def modulus(first: float, second: float) -> float:
    """Return Python's remainder after division."""
    first, second = validate_operands(first, second)
    if second == 0:
        raise OperationError("Cannot calculate modulus with a zero divisor.")
    return _finite_result(first % second)


def int_divide(first: float, second: float) -> int:
    """Return the quotient with its fractional part truncated toward zero."""
    first, second = validate_operands(first, second)
    if second == 0:
        raise OperationError("Cannot perform integer division by zero.")
    return math.trunc(_finite_result(first / second))


def percent(first: float, second: float) -> float:
    """Return the first number as a percentage of the second."""
    first, second = validate_operands(first, second)
    if second == 0:
        raise OperationError("Cannot calculate a percentage with a zero denominator.")
    return _finite_result((first / second) * 100)


def abs_diff(first: float, second: float) -> float:
    """Return the absolute difference between the operands."""
    first, second = validate_operands(first, second)
    return _finite_result(abs(first - second))


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


class ModulusOperation:
    def execute(self, first: float, second: float) -> float:
        return modulus(first, second)


class IntegerDivisionOperation:
    def execute(self, first: float, second: float) -> int:
        return int_divide(first, second)


class PercentOperation:
    def execute(self, first: float, second: float) -> float:
        return percent(first, second)


class AbsoluteDifferenceOperation:
    def execute(self, first: float, second: float) -> float:
        return abs_diff(first, second)


class OperationFactory:
    """Create an operation object from its user-facing name."""

    _operations: dict[str, type[Operation]] = {
        "add": AddOperation,
        "subtract": SubtractOperation,
        "multiply": MultiplyOperation,
        "divide": DivideOperation,
        "power": PowerOperation,
        "root": RootOperation,
        "modulus": ModulusOperation,
        "int_divide": IntegerDivisionOperation,
        "percent": PercentOperation,
        "abs_diff": AbsoluteDifferenceOperation,
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
