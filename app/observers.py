"""Observers of newly completed calculations."""

import os
from typing import TYPE_CHECKING, Protocol

from app.calculation import Calculation
from app.logger import Logger

if TYPE_CHECKING:
    from app.calculator import Calculator


class CalculationObserver(Protocol):
    """Receive one notification after a successful calculation is recorded."""

    def on_calculation(self, calculation: Calculation, calculator: "Calculator") -> None: ...


class LoggingObserver:
    """Log the operation, operands, and result of each completed calculation."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def on_calculation(self, calculation: Calculation, calculator: "Calculator") -> None:
        self._logger.info(
            "Calculated %s(%s, %s) = %s",
            calculation.operation, calculation.first, calculation.second, calculation.result,
        )


class AutoSaveObserver:
    """Persist full history after each new calculation when enabled."""

    def __init__(self, path: str | os.PathLike[str], encoding: str = "utf-8", enabled: bool = True) -> None:
        self.path = path
        self.encoding = encoding
        self.enabled = enabled

    def on_calculation(self, calculation: Calculation, calculator: "Calculator") -> None:
        if self.enabled:
            calculator.save_history(self.path, self.encoding)
