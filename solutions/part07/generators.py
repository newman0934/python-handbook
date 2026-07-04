"""Part 7 練習:generator(承 03-generator / 07-lazy-evaluation)。"""

from __future__ import annotations

from collections.abc import Iterable, Iterator


def countdown(n: int) -> Iterator[int]:
    """從 n 遞減到 1。"""
    while n > 0:
        yield n
        n -= 1


def fib() -> Iterator[int]:
    """無限費氏數列:0,1,1,2,3,5,..."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def take[T](it: Iterable[T], n: int) -> list[T]:
    """從可迭代物件取前 n 個(對無限序列也安全)。"""
    out: list[T] = []
    for i, x in enumerate(it):
        if i >= n:
            break
        out.append(x)
    return out
