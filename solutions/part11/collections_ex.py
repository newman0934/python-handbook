"""Part 11 練習:collections(承 09-collections-functools-itertools)。"""

from __future__ import annotations

from collections import Counter


def most_common(items: list[str], n: int) -> list[tuple[str, int]]:
    """回傳出現次數最多的前 n 個 (item, count)。"""
    return Counter(items).most_common(n)


def merge_counts(dicts: list[dict[str, int]]) -> dict[str, int]:
    """把多個計數 dict 相加合併。"""
    total: Counter[str] = Counter()
    for d in dicts:
        total.update(d)
    return dict(total)
