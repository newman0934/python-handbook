"""Part 11 練習:collections(承 09-collections-functools-itertools)。

實作 most_common(用 collections.Counter 取前 n 名)與 merge_counts(相加合併多個計數 dict)。
"""

from __future__ import annotations


def most_common(items: list[str], n: int) -> list[tuple[str, int]]:
    """回傳出現次數最多的前 n 個 (item, count)。"""
    raise NotImplementedError("實作我!")


def merge_counts(dicts: list[dict[str, int]]) -> dict[str, int]:
    """把多個計數 dict 相加合併。"""
    raise NotImplementedError("實作我!")
