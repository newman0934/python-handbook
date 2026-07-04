"""Part 7 練習:generator(承 03-generator / 07-lazy-evaluation)。

實作 countdown(遞減)、fib(無限費氏,用 yield)、take(取前 n 個,對無限序列安全)。
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator


def countdown(n: int) -> Iterator[int]:
    """從 n 遞減到 1。"""
    raise NotImplementedError("實作我!")


def fib() -> Iterator[int]:
    """無限費氏數列:0,1,1,2,3,5,..."""
    raise NotImplementedError("實作我!")


def take[T](it: Iterable[T], n: int) -> list[T]:
    """從可迭代物件取前 n 個(對無限序列也安全)。"""
    raise NotImplementedError("實作我!")
