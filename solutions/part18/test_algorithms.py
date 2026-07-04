"""Part 18 algorithms 測試。"""

from __future__ import annotations

from solutions.part18.algorithms import first_non_repeating, has_duplicate, two_sum


def test_two_sum_found() -> None:
    assert two_sum([2, 7, 11, 15], 9) == (0, 1)


def test_two_sum_none() -> None:
    assert two_sum([1, 2, 3], 100) is None


def test_has_duplicate() -> None:
    assert has_duplicate([1, 2, 3, 2]) is True
    assert has_duplicate([1, 2, 3]) is False


def test_first_non_repeating() -> None:
    assert first_non_repeating("leetcode") == "l"
    assert first_non_repeating("aabb") is None
