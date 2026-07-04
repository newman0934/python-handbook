"""Part 8 練習:decorator(承 03-decorator-basics / 05-functools)。"""

from __future__ import annotations

import functools
from collections.abc import Callable


def double_result(func: Callable[[int], int]) -> Callable[[int], int]:
    """裝飾器:把被裝飾函式的回傳值乘以 2。"""

    @functools.wraps(func)
    def wrapper(x: int) -> int:
        return func(x) * 2

    return wrapper


def memoize(func: Callable[[int], int]) -> Callable[[int], int]:
    """裝飾器:以參數為 key 快取結果(int -> int)。"""
    cache: dict[int, int] = {}

    @functools.wraps(func)
    def wrapper(n: int) -> int:
        if n not in cache:
            cache[n] = func(n)
        return cache[n]

    return wrapper
