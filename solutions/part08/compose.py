"""Part 8 練習:函式組合(承 02-higher-order-functions)。"""

from __future__ import annotations

from collections.abc import Callable


def compose(*funcs: Callable[[int], int]) -> Callable[[int], int]:
    """由右到左組合函式:compose(f, g)(x) == f(g(x))。無參數時回傳原值。"""

    def composed(x: int) -> int:
        for f in reversed(funcs):
            x = f(x)
        return x

    return composed
