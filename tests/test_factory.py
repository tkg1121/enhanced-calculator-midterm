"""Tests for selecting the basic operation objects."""

import pytest

from app.exceptions import OperationError
from app.operations import (
    AddOperation,
    DivideOperation,
    MultiplyOperation,
    OperationFactory,
    PowerOperation,
    RootOperation,
    SubtractOperation,
)


@pytest.mark.parametrize(
    "name,operation_type,expected",
    [
        ("add", AddOperation, 5),
        (" SUBTRACT ", SubtractOperation, -1),
        ("multiply", MultiplyOperation, 6),
        ("divide", DivideOperation, 2 / 3),
        ("power", PowerOperation, 8),
        ("root", RootOperation, 2 ** (1 / 3)),
    ],
)
def test_factory_creates_basic_operations(name, operation_type, expected):
    operation = OperationFactory.create(name)
    assert isinstance(operation, operation_type)
    assert operation.execute(2, 3) == pytest.approx(expected)


def test_factory_creates_distinct_instances():
    assert OperationFactory.create("add") is not OperationFactory.create("add")


@pytest.mark.parametrize("name", ["", "square", None])
def test_factory_rejects_unsupported_names(name):
    with pytest.raises(OperationError, match="operation|Operation"):
        OperationFactory.create(name)
