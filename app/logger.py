"""File-backed calculator logging without changing root logging settings."""

import logging
import os
from pathlib import Path


class Logger:
    """Write calculator events to one reusable handler per file path."""

    def __init__(self, path: str | os.PathLike[str], encoding: str = "utf-8") -> None:
        destination = Path(path).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(f"enhanced_calculator.{destination}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
        if not any(isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == destination
                   for handler in self._logger.handlers):
            handler = logging.FileHandler(destination, encoding=encoding)
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self._logger.addHandler(handler)

    def info(self, message: str, *args: object) -> None:
        self._logger.info(message, *args)

    def warning(self, message: str, *args: object) -> None:
        self._logger.warning(message, *args)

    def error(self, message: str, *args: object) -> None:
        self._logger.error(message, *args)
