"""Part 5 unique_by 測試。"""

from __future__ import annotations

from solutions.part05.unique_by import unique_by


def test_unique_by_length() -> None:
    assert unique_by(["a", "bb", "cc", "d"], key=len) == ["a", "bb"]


def test_unique_by_identity() -> None:
    assert unique_by([1, 1, 2, 3, 2], key=lambda x: x) == [1, 2, 3]


def test_empty() -> None:
    assert unique_by([], key=len) == []
