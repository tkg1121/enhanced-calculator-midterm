"""Tests for ordered in-memory history."""

from dataclasses import FrozenInstanceError

import pytest

from app.calculation import Calculation
from app.history import History


def test_history_starts_empty_and_keeps_order():
    history = History()
    assert history.entries() == ()
    first = Calculation.create("add", 2, 3)
    second = Calculation.create("multiply", 4, 5)
    history.append(first)
    history.append(second)
    assert history.entries() == (first, second)


def test_returned_history_is_independent_and_immutable():
    history = History()
    history.append(Calculation.create("add", 2, 3))
    saved = history.entries()
    history.append(Calculation.create("multiply", 4, 5))
    assert len(saved) == 1
    with pytest.raises(FrozenInstanceError):
        saved[0].result = 999
    assert history.entries()[0].result == 5


def test_clear_reports_whether_history_changed():
    history = History()
    assert history.clear() is False
    history.append(Calculation.create("add", 2, 3))
    assert history.clear() is True
    assert history.entries() == ()
