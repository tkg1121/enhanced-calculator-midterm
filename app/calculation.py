"""Immutable records of completed calculations."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.input_validators import validate_operands
from app.operations import OperationFactory


@dataclass(frozen=True)
class Calculation:
    """The operation, validated operands, and result of one calculation."""

    operation: str
    first: float
    second: float
    result: float | int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls, operation: str, first: object, second: object,
        *, max_input_value: float | None = None, precision: int | None = None,
    ) -> "Calculation":
        """Calculate successfully before constructing a history record."""
        selected = OperationFactory.create(operation)
        first, second = validate_operands(first, second, max_input_value)
        result = selected.execute(first, second)
        if precision is not None and not isinstance(result, int):
            result = round(result, precision)
        return cls(operation.strip().lower(), first, second, result)
