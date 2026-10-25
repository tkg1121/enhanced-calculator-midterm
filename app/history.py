"""In-memory storage for completed calculations."""

from app.calculation import Calculation


class History:
    """Own the ordered, mutable collection of calculation records."""

    def __init__(self, max_size: int | None = None) -> None:
        self._entries: list[Calculation] = []
        self._max_size = max_size

    def append(self, entry: Calculation) -> None:
        self._entries.append(entry)
        if self._max_size is not None and len(self._entries) > self._max_size:
            del self._entries[:-self._max_size]

    def entries(self) -> tuple[Calculation, ...]:
        """Return an immutable view that cannot alter stored history."""
        return tuple(self._entries)

    def restore(self, entries: tuple[Calculation, ...]) -> None:
        """Replace live history with a fresh list of snapshot entries."""
        self._entries = list(entries[-self._max_size:] if self._max_size is not None else entries)

    def clear(self) -> bool:
        """Remove existing entries and report whether anything changed."""
        if not self._entries:
            return False
        self._entries.clear()
        return True
