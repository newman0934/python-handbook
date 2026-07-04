"""Part 8 練習:函式組合(承 02-higher-order-functions)。

實作 compose:由右到左套用函式,compose(f, g)(x) == f(g(x))。
"""

from __future__ import annotations

from collections.abc import Callable


def compose(*funcs: Callable[[int], int]) -> Callable[[int], int]:
    """由右到左組合函式:compose(f, g)(x) == f(g(x))。無參數時回傳原值。"""
    raise NotImplementedError("實作我!")
