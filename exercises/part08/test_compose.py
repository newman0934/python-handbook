"""Part 8 compose 測試。"""

from __future__ import annotations

from exercises.part08.compose import compose


def _add1(x: int) -> int:
    return x + 1


def _mul2(x: int) -> int:
    return x * 2


def test_compose_order() -> None:
    # compose(add1, mul2)(3) == add1(mul2(3)) == 7
    assert compose(_add1, _mul2)(3) == 7


def test_compose_reversed_order() -> None:
    # compose(mul2, add1)(3) == mul2(add1(3)) == 8
    assert compose(_mul2, _add1)(3) == 8


def test_compose_empty_identity() -> None:
    assert compose()(42) == 42
