"""Part 18 練習:用資料結構降複雜度(承 效能與複雜度)。"""

from __future__ import annotations


def two_sum(nums: list[int], target: int) -> tuple[int, int] | None:
    """回傳兩個索引 (i, j) 使 nums[i]+nums[j]==target;無解回 None。

    用 dict 達到 O(n),而非 O(n^2) 雙迴圈。
    """
    seen: dict[int, int] = {}
    for i, n in enumerate(nums):
        need = target - n
        if need in seen:
            return (seen[need], i)
        seen[n] = i
    return None


def has_duplicate(items: list[int]) -> bool:
    """是否有重複元素(用 set,O(n))。"""
    return len(set(items)) != len(items)


def first_non_repeating(text: str) -> str | None:
    """回傳第一個只出現一次的字元;沒有則 None。"""
    counts: dict[str, int] = {}
    for ch in text:
        counts[ch] = counts.get(ch, 0) + 1
    for ch in text:
        if counts[ch] == 1:
            return ch
    return None
