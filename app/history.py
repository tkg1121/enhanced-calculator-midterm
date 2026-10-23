"""In-memory storage for completed calculations."""

from app.calculation import Calculation


class History:
    """Own the ordered, mutable collection of calculation records."""

    def __init__(self) -> None:
        self._entries: list[Calculation] = []

    def append(self, entry: Calculation) -> None:
        self._entries.append(entry)

    def entries(self) -> tuple[Calculation, ...]:
        """Return an immutable view that cannot alter stored history."""
        return tuple(self._entries)

    def restore(self, entries: tuple[Calculation, ...]) -> None:
        """Replace live history with a fresh list of snapshot entries."""
        self._entries = list(entries)

    def clear(self) -> bool:
        """Remove existing entries and report whether anything changed."""
        if not self._entries:
            return False
        self._entries.clear()
        return True
