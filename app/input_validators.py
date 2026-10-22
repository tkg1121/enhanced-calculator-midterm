"""Shared operand conversion and validation."""

import math

from app.exceptions import ValidationError


def validate_number(value: object) -> float:
    """Convert a numeric value or numeric string to a finite float."""
    if isinstance(value, bool):
        raise ValidationError("Boolean values are not valid numbers.")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValidationError("Enter a real number, such as 4 or -2.5.") from error
    if not math.isfinite(number):
        raise ValidationError("Numbers must be finite; NaN and infinity are invalid.")
    return number


def validate_operands(first: object, second: object) -> tuple[float, float]:
    """Validate exactly two operands for a binary operation."""
    return validate_number(first), validate_number(second)
