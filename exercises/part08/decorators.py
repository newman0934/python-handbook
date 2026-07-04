"""Part 8 練習:decorator(承 03-decorator-basics / 05-functools)。

實作 double_result(回傳值 x2)與 memoize(快取 int->int 結果)。
提示:用 functools.wraps 保留原函式 metadata。
"""

from __future__ import annotations

from collections.abc import Callable


def double_result(func: Callable[[int], int]) -> Callable[[int], int]:
    """裝飾器:把被裝飾函式的回傳值乘以 2。"""
    raise NotImplementedError("實作我!")


def memoize(func: Callable[[int], int]) -> Callable[[int], int]:
    """裝飾器:以參數為 key 快取結果(int -> int)。"""
    raise NotImplementedError("實作我!")
