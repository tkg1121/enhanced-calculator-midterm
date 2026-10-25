"""Validated pandas CSV storage for calculation history."""

import os
import warnings
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd

from app.calculation import Calculation
from app.exceptions import CalculatorError, PersistenceError
from app.input_validators import validate_number, validate_operands
from app.operations import OperationFactory


COLUMNS = ("operation", "first", "second", "result", "timestamp")


def save_history(entries: tuple[Calculation, ...], path: str | os.PathLike[str], encoding: str = "utf-8") -> None:
    """Atomically replace a CSV after pandas finishes writing all entries."""
    destination = Path(path)
    temporary: Path | None = None
    try:
        if any(entry.timestamp.tzinfo is None or entry.timestamp.utcoffset() is None for entry in entries):
            raise ValueError("Calculation timestamps must include a timezone offset")
        rows = [
            {
                "operation": entry.operation,
                "first": repr(entry.first),
                "second": repr(entry.second),
                "result": repr(entry.result),
                "timestamp": entry.timestamp.astimezone(timezone.utc).isoformat(),
            }
            for entry in entries
        ]
        frame = pd.DataFrame(rows, columns=COLUMNS)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            mode="w", encoding=encoding, newline="", dir=destination.parent,
            prefix=f".{destination.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            frame.to_csv(stream, index=False)
        os.replace(temporary, destination)
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError, LookupError) as error:
        raise PersistenceError(f"Could not save history to {destination}: {error}") from error
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def load_history(path: str | os.PathLike[str], encoding: str = "utf-8") -> tuple[Calculation, ...]:
    """Validate every CSV row before returning immutable records."""
    source = Path(path)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", pd.errors.ParserWarning)
            frame = pd.read_csv(source, dtype=str, keep_default_na=False, encoding=encoding, index_col=False)
    except (OSError, UnicodeError, ValueError, LookupError, pd.errors.ParserError, pd.errors.ParserWarning) as error:
        raise PersistenceError(f"Could not load history from {source}: {error}") from error

    missing = set(COLUMNS) - set(frame.columns)
    if missing:
        raise PersistenceError(f"History CSV is missing columns: {', '.join(sorted(missing))}.")
    entries = []
    for row_number, row in enumerate(frame.to_dict(orient="records"), start=2):
        try:
            operation = row["operation"]
            selected = OperationFactory.create(operation)
            first, second = validate_operands(row["first"], row["second"])
            expected = selected.execute(first, second)
            result = int(row["result"]) if isinstance(expected, int) else validate_number(row["result"])
            if result != expected and not (
                isinstance(expected, float) and any(result == round(expected, places) for places in range(18))
            ):
                raise ValueError("result does not match the operation and operands")
            timestamp = datetime.fromisoformat(row["timestamp"])
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError("timestamp must include a timezone offset")
            entries.append(Calculation(operation.strip().lower(), first, second, result, timestamp.astimezone(timezone.utc)))
        except (CalculatorError, ValueError, TypeError, OverflowError) as error:
            raise PersistenceError(f"Invalid history record on CSV row {row_number}: {error}") from error
    return tuple(entries)
