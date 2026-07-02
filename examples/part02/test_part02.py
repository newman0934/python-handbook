"""Part 2 範例的驗證測試。

執行：pytest examples/part02
"""

import math
from decimal import Decimal

import pytest

from examples.part02.fundamentals import (
    append_bad,
    append_good,
    frozen_closures,
    make_counter,
    make_multiplier,
    money_total,
    with_tax,
)


def test_mutable_default_trap_accumulates() -> None:
    # 陷阱：第二次呼叫殘留上次結果
    assert append_bad(1) == [1]
    assert append_bad(2) == [1, 2]


def test_mutable_default_fixed_is_independent() -> None:
    assert append_good(1) == [1]
    assert append_good(2) == [2]


@pytest.mark.parametrize(
    ("factor", "x", "expected"),
    [(2, 10, 20), (3, 10, 30), (5, 4, 20)],
)
def test_closure_multiplier(factor: int, x: int, expected: int) -> None:
    assert make_multiplier(factor)(x) == expected


def test_closure_counter_keeps_state() -> None:
    counter = make_counter()
    assert [counter(), counter(), counter()] == [1, 2, 3]


def test_float_needs_isclose() -> None:
    assert (0.1 + 0.2) != 0.3
    assert math.isclose(0.1 + 0.2, 0.3)


def test_decimal_is_exact() -> None:
    assert money_total(["19.99", "5.01", "0.50"]) == Decimal("25.50")


def test_with_tax_quantizes() -> None:
    assert with_tax("19.99", "0.05") == Decimal("20.99")


def test_frozen_closures() -> None:
    assert frozen_closures() == [0, 1, 2]
