"""Immutable records of completed calculations."""

from dataclasses import dataclass

from app.input_validators import validate_operands
from app.operations import OperationFactory


@dataclass(frozen=True)
class Calculation:
    """The operation, validated operands, and result of one calculation."""

    operation: str
    first: float
    second: float
    result: float | int

    @classmethod
    def create(cls, operation: str, first: object, second: object) -> "Calculation":
        """Calculate successfully before constructing a history record."""
        selected = OperationFactory.create(operation)
        first, second = validate_operands(first, second)
        result = selected.execute(first, second)
        return cls(operation.strip().lower(), first, second, result)
