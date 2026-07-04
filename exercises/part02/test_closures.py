"""Part 2 closures 測試。"""

from __future__ import annotations

from exercises.part02.closures import make_accumulator, make_counter


def test_counter_increments() -> None:
    c = make_counter()
    assert [c(), c(), c()] == [1, 2, 3]


def test_counter_start() -> None:
    c = make_counter(10)
    assert c() == 11


def test_counters_independent() -> None:
    a, b = make_counter(), make_counter()
    a()
    a()
    assert b() == 1


def test_accumulator() -> None:
    acc = make_accumulator()
    assert [acc(10), acc(5), acc(-3)] == [10, 15, 12]
