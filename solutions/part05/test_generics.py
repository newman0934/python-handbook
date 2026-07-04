"""Part 5 generics 測試。"""

from __future__ import annotations

from solutions.part05.generics import first, last


def test_first() -> None:
    assert first([1, 2, 3]) == 1
    assert first(["a"]) == "a"


def test_last() -> None:
    assert last([1, 2, 3]) == 3


def test_empty_returns_none() -> None:
    assert first([]) is None
    assert last([]) is None
