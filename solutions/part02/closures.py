"""Part 2 練習:閉包(承 12-closures)。"""

from __future__ import annotations

from collections.abc import Callable


def make_counter(start: int = 0) -> Callable[[], int]:
    """回傳一個計數器函式:每次呼叫回傳遞增後的值(從 start+1 開始)。

    多個 counter 之間狀態彼此獨立。
    """
    count = start

    def counter() -> int:
        nonlocal count
        count += 1
        return count

    return counter


def make_accumulator() -> Callable[[int], int]:
    """回傳一個累加器:每次呼叫把參數加進總和並回傳當前總和。"""
    total = 0

    def add(x: int) -> int:
        nonlocal total
        total += x
        return total

    return add
