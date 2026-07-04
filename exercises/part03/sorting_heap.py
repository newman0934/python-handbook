"""Part 3 練習:排序與 heap(承 11-sorting / 12-heapq-bisect)。

實作 top_k(用 heapq)與 merge_intervals(用 sorted)讓測試轉綠。
"""

from __future__ import annotations


def top_k(nums: list[int], k: int) -> list[int]:
    """回傳最大的 k 個數(由大到小)。k<=0 回 []。"""
    raise NotImplementedError("實作我!")


def merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """合併重疊區間。intervals 為 (start, end);回傳排序後合併的區間。"""
    raise NotImplementedError("實作我!")
