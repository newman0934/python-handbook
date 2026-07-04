"""Part 3 sequences 測試。"""

from __future__ import annotations

import pytest

from exercises.part03.sequences import chunk, dedup


def test_dedup_preserves_order() -> None:
    assert dedup([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_dedup_empty() -> None:
    assert dedup([]) == []


def test_chunk() -> None:
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_chunk_invalid_size() -> None:
    with pytest.raises(ValueError):
        chunk([1, 2], 0)
