"""Part 3 資料結構的可執行範例。

對應章節：chapters/03-data-structures/
"""

from __future__ import annotations

import bisect
import copy
import heapq
from collections import Counter, defaultdict
from dataclasses import dataclass
from operator import itemgetter


def build_matrix(rows: int, cols: int) -> list[list[int]]:
    """正確建立獨立的二維 list（避免 [[0]*c]*r 別名陷阱）。"""
    return [[0] * cols for _ in range(rows)]


def dedupe_keep_order(items: list[int]) -> list[int]:
    """去重且保留順序（set 不保證順序，用 dict.fromkeys）。"""
    return list(dict.fromkeys(items))


def group_by_length(words: list[str]) -> dict[int, list[str]]:
    """用 defaultdict 依長度分組。"""
    groups: defaultdict[int, list[str]] = defaultdict(list)
    for w in words:
        groups[len(w)].append(w)
    return dict(groups)


def word_count(text: str) -> dict[str, int]:
    """用 Counter 計數。"""
    return dict(Counter(text.lower().split()))


def shallow_leaks_inner() -> list[list[int]]:
    """展示淺複製後改內層會影響原本，回傳被影響的原本。"""
    original = [[1, 2], [3, 4]]
    shallow = original.copy()
    shallow[0].append(99)
    return original


def deep_is_isolated() -> list[list[int]]:
    """展示深複製後改內層不影響原本，回傳未受影響的原本。"""
    original = [[1, 2], [3, 4]]
    deep = copy.deepcopy(original)
    deep[0].append(99)
    return original


@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int


def sort_by_second(pairs: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """用 operator.itemgetter 依第二欄排序。"""
    return sorted(pairs, key=itemgetter(1))


def grade(score: int) -> str:
    """用 bisect 把分數轉等第。"""
    breakpoints = [60, 70, 80, 90]
    grades = "FDCBA"
    return grades[bisect.bisect_right(breakpoints, score)]


def k_largest(nums: list[int], k: int) -> list[int]:
    """用 heapq 取最大的 k 個。"""
    return heapq.nlargest(k, nums)
