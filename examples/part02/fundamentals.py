"""Part 2 語言基礎的可執行範例。

對應章節：chapters/02-fundamentals/
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal


def append_bad(item: int, target: list[int] = []) -> list[int]:  # noqa: B006
    """反例：可變預設參數陷阱（跨呼叫共用同一 list）。"""
    target.append(item)
    return target


def append_good(item: int, target: list[int] | None = None) -> list[int]:
    """正解：用 None 哨兵，每次呼叫建立新 list。"""
    if target is None:
        target = []
    target.append(item)
    return target


def make_multiplier(factor: int) -> Callable[[int], int]:
    """閉包：回傳記住 factor 的函式。"""

    def multiply(x: int) -> int:
        return x * factor

    return multiply


def make_counter() -> Callable[[], int]:
    """閉包 + nonlocal：保持狀態的計數器。"""
    count = 0

    def increment() -> int:
        nonlocal count
        count += 1
        return count

    return increment


def money_total(prices: list[str]) -> Decimal:
    """用 Decimal 精確加總金額（字串輸入）。"""
    return sum((Decimal(p) for p in prices), start=Decimal("0"))


def with_tax(price: str, rate: str) -> Decimal:
    """含稅並量化到分、四捨五入。"""
    total = Decimal(price) * (Decimal("1") + Decimal(rate))
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def frozen_closures() -> list[int]:
    """修正迴圈閉包陷阱：用工廠函式製造獨立作用域。"""

    def make(i: int) -> Callable[[], int]:
        return lambda: i

    funcs = [make(i) for i in range(3)]
    return [f() for f in funcs]
