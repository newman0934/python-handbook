"""Part 3 sorting_heap 測試。"""

from __future__ import annotations

from exercises.part03.sorting_heap import merge_intervals, top_k


def test_top_k() -> None:
    assert top_k([3, 1, 4, 1, 5, 9, 2, 6], 3) == [9, 6, 5]


def test_top_k_zero() -> None:
    assert top_k([1, 2, 3], 0) == []


def test_merge_intervals() -> None:
    assert merge_intervals([(1, 3), (2, 6), (8, 10), (15, 18)]) == [
        (1, 6),
        (8, 10),
        (15, 18),
    ]


def test_merge_intervals_empty() -> None:
    assert merge_intervals([]) == []
