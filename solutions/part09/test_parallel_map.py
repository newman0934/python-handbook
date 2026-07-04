"""Part 9 parallel_map 測試。"""

from __future__ import annotations

from solutions.part09.parallel_map import parallel_map


def test_parallel_map_squares() -> None:
    assert parallel_map(lambda x: x * x, [1, 2, 3, 4]) == [1, 4, 9, 16]


def test_preserves_order() -> None:
    assert parallel_map(lambda x: x + 1, list(range(20))) == list(range(1, 21))


def test_empty() -> None:
    assert parallel_map(lambda x: x, []) == []
