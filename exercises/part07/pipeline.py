"""Part 7 練習:惰性管線(承 04-generator-expression / 06-itertools)。

實作 chunked(惰性分塊,size<=0 丟 ValueError)與 running_max(累計最大值)。
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator


def chunked[T](items: Iterable[T], size: int) -> Iterator[list[T]]:
    """把可迭代物件分成每塊 size 個(惰性,最後一塊可較短)。"""
    raise NotImplementedError("實作我!")


def running_max(nums: Iterable[int]) -> Iterator[int]:
    """回傳到目前為止的最大值序列。"""
    raise NotImplementedError("實作我!")
