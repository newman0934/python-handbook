"""Part 7 generators 測試。"""

from __future__ import annotations

from exercises.part07.generators import countdown, fib, take


def test_countdown() -> None:
    assert list(countdown(3)) == [3, 2, 1]


def test_take_from_infinite_fib() -> None:
    assert take(fib(), 10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


def test_take_more_than_available() -> None:
    assert take(countdown(2), 10) == [2, 1]
