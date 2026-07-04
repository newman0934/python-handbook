"""Part 7 練習:惰性管線(承 04-generator-expression / 06-itertools)。"""

from __future__ import annotations

from collections.abc import Iterable, Iterator


def chunked[T](items: Iterable[T], size: int) -> Iterator[list[T]]:
    """把可迭代物件分成每塊 size 個(惰性,最後一塊可較短)。"""
    if size <= 0:
        raise ValueError("size 必須 > 0")
    chunk: list[T] = []
    for x in items:
        chunk.append(x)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def running_max(nums: Iterable[int]) -> Iterator[int]:
    """回傳到目前為止的最大值序列。"""
    current: int | None = None
    for x in nums:
        current = x if current is None else max(current, x)
        yield current
