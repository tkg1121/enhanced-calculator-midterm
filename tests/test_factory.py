"""Tests for selecting the basic operation objects."""

import pytest

from app.exceptions import OperationError, ValidationError
from app.operations import (
    AbsoluteDifferenceOperation,
    AddOperation,
    DivideOperation,
    IntegerDivisionOperation,
    ModulusOperation,
    MultiplyOperation,
    OperationFactory,
    PercentOperation,
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
        ("modulus", ModulusOperation, 2),
        ("int_divide", IntegerDivisionOperation, 0),
        ("percent", PercentOperation, 200 / 3),
        ("abs_diff", AbsoluteDifferenceOperation, 1),
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


def test_factory_operation_validates_operands():
    with pytest.raises(ValidationError):
        OperationFactory.create("add").execute("nan", 2)
