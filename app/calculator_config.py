"""Validated settings from a .env file, the process environment, and overrides."""

import codecs
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values

from app.exceptions import ConfigurationError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = {
    "CALCULATOR_LOG_DIR": "logs",
    "CALCULATOR_HISTORY_DIR": "data",
    "CALCULATOR_MAX_HISTORY_SIZE": "1000",
    "CALCULATOR_AUTO_SAVE": "false",
    "CALCULATOR_PRECISION": "15",
    "CALCULATOR_MAX_INPUT_VALUE": "1e308",
    "CALCULATOR_DEFAULT_ENCODING": "utf-8",
    "CALCULATOR_LOG_FILE": "calculator.log",
    "CALCULATOR_HISTORY_FILE": "history.csv",
}


def _integer(value: object, name: str, minimum: int) -> int:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError) as error:
        raise ConfigurationError(f"{name} must be an integer of at least {minimum}.") from error
    if parsed < minimum:
        raise ConfigurationError(f"{name} must be an integer of at least {minimum}.")
    return parsed


def _directory(value: object, name: str, base_dir: Path) -> Path:
    if value is None or not str(value).strip():
        raise ConfigurationError(f"{name} must be a nonempty directory path.")
    path = Path(str(value)).expanduser()
    path = (path if path.is_absolute() else base_dir / path).resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ConfigurationError(f"Cannot create {name} at {path}: {error}") from error
    return path


def _file(value: object, name: str, directory: Path) -> Path:
    if value is None or not str(value).strip():
        raise ConfigurationError(f"{name} must be a nonempty file path.")
    path = Path(str(value)).expanduser()
    path = (path if path.is_absolute() else directory / path).resolve()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            raise ConfigurationError(f"{name} points to a directory: {path}.")
    except OSError as error:
        raise ConfigurationError(f"Cannot use {name} at {path}: {error}") from error
    return path


@dataclass(frozen=True)
class CalculatorConfig:
    """Settings validated before use by the calculator or command-line app."""

    log_dir: Path
    history_dir: Path
    max_history_size: int
    auto_save: bool
    precision: int
    max_input_value: float
    encoding: str
    log_file: Path
    history_file: Path

    @classmethod
    def load(
        cls,
        env_file: str | os.PathLike[str] | None = None,
        *,
        overrides: Mapping[str, object] | None = None,
        environ: Mapping[str, str] | None = None,
        base_dir: str | os.PathLike[str] = PROJECT_ROOT,
    ) -> "CalculatorConfig":
        """Use defaults < .env < process environment < explicit overrides."""
        base = Path(base_dir).resolve()
        source = Path(env_file) if env_file is not None else base / ".env"
        if not source.is_absolute():
            source = base / source
        if source.exists() and not source.is_file():
            raise ConfigurationError(f"Environment path is not a file: {source}.")
        try:
            from_file = dotenv_values(source) if source.exists() else {}
        except OSError as error:
            raise ConfigurationError(f"Could not read environment file {source}: {error}") from error
        process = os.environ if environ is None else environ
        unknown = set(overrides or {}) - DEFAULTS.keys()
        if unknown:
            raise ConfigurationError(f"Unknown configuration setting: {', '.join(sorted(unknown))}.")
        values: dict[str, object] = dict(DEFAULTS)
        values.update({key: value for key, value in from_file.items() if key in DEFAULTS})
        values.update({key: process[key] for key in DEFAULTS if key in process})
        values.update(overrides or {})

        size = _integer(values["CALCULATOR_MAX_HISTORY_SIZE"], "CALCULATOR_MAX_HISTORY_SIZE", 1)
        precision = _integer(values["CALCULATOR_PRECISION"], "CALCULATOR_PRECISION", 0)
        try:
            max_input = float(values["CALCULATOR_MAX_INPUT_VALUE"])
        except (TypeError, ValueError, OverflowError) as error:
            raise ConfigurationError("CALCULATOR_MAX_INPUT_VALUE must be positive and finite.") from error
        if not math.isfinite(max_input) or max_input <= 0:
            raise ConfigurationError("CALCULATOR_MAX_INPUT_VALUE must be positive and finite.")
        auto_save_text = str(values["CALCULATOR_AUTO_SAVE"]).strip().lower()
        if auto_save_text not in {"true", "false"}:
            raise ConfigurationError("CALCULATOR_AUTO_SAVE must be true or false.")
        encoding = values["CALCULATOR_DEFAULT_ENCODING"]
        try:
            codecs.lookup(str(encoding))
        except LookupError as error:
            raise ConfigurationError("CALCULATOR_DEFAULT_ENCODING must name a recognized encoding.") from error
        if not encoding or not str(encoding).strip():
            raise ConfigurationError("CALCULATOR_DEFAULT_ENCODING must name a recognized encoding.")

        log_dir = _directory(values["CALCULATOR_LOG_DIR"], "CALCULATOR_LOG_DIR", base)
        history_dir = _directory(values["CALCULATOR_HISTORY_DIR"], "CALCULATOR_HISTORY_DIR", base)
        log_file = _file(values["CALCULATOR_LOG_FILE"], "CALCULATOR_LOG_FILE", log_dir)
        history_file = _file(values["CALCULATOR_HISTORY_FILE"], "CALCULATOR_HISTORY_FILE", history_dir)
        return cls(log_dir, history_dir, size, auto_save_text == "true", precision,
                   max_input, str(encoding), log_file, history_file)
