"""Part 18 練習:用資料結構降複雜度(承 效能與複雜度)。

實作 two_sum(用 dict 達 O(n))、has_duplicate(用 set)、
first_non_repeating(第一個只出現一次的字元)。
"""

from __future__ import annotations


def two_sum(nums: list[int], target: int) -> tuple[int, int] | None:
    """回傳兩個索引 (i, j) 使 nums[i]+nums[j]==target;無解回 None。"""
    raise NotImplementedError("實作我!")


def has_duplicate(items: list[int]) -> bool:
    """是否有重複元素(用 set,O(n))。"""
    raise NotImplementedError("實作我!")


def first_non_repeating(text: str) -> str | None:
    """回傳第一個只出現一次的字元;沒有則 None。"""
    raise NotImplementedError("實作我!")
