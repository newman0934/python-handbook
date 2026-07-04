"""Part 3 練習:排序與 heap(承 11-sorting / 12-heapq-bisect)。"""

from __future__ import annotations

import heapq


def top_k(nums: list[int], k: int) -> list[int]:
    """回傳最大的 k 個數(由大到小)。k<=0 回 []。"""
    if k <= 0:
        return []
    return heapq.nlargest(k, nums)


def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """合併重疊區間。intervals 為 (start, end);回傳排序後合併的區間。"""
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged: list[tuple[int, int]] = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged
