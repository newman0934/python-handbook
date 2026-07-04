"""Part 11 collections_ex 測試。"""

from __future__ import annotations

from solutions.part11.collections_ex import merge_counts, most_common


def test_most_common() -> None:
    assert most_common(["a", "b", "a", "c", "a", "b"], 2) == [("a", 3), ("b", 2)]


def test_merge_counts() -> None:
    assert merge_counts([{"a": 1, "b": 2}, {"a": 3, "c": 1}]) == {"a": 4, "b": 2, "c": 1}


def test_merge_counts_empty() -> None:
    assert merge_counts([]) == {}
