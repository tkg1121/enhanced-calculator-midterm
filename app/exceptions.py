"""Errors raised by the calculator's public API."""


class CalculatorError(Exception):
    """Base class for errors callers may handle together."""


class ValidationError(CalculatorError):
    """An operand cannot be used as a finite real number."""


class OperationError(CalculatorError):
    """An operation name or mathematical result is invalid."""


class PersistenceError(CalculatorError):
    """History could not be saved or loaded."""
