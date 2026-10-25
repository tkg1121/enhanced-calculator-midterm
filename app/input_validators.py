"""Shared operand conversion and validation."""

import math

from app.exceptions import ValidationError


def validate_number(value: object, max_value: float | None = None) -> float:
    """Convert a numeric value or numeric string to a finite float."""
    if isinstance(value, bool):
        raise ValidationError("Boolean values are not valid numbers.")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValidationError("Enter a real number, such as 4 or -2.5.") from error
    if not math.isfinite(number):
        raise ValidationError("Numbers must be finite; NaN and infinity are invalid.")
    if max_value is not None and abs(number) > max_value:
        raise ValidationError(f"Input magnitude must not exceed {max_value}.")
    return number


def validate_operands(first: object, second: object, max_value: float | None = None) -> tuple[float, float]:
    """Validate exactly two operands for a binary operation."""
    return validate_number(first, max_value), validate_number(second, max_value)
