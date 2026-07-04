"""Part 2 comprehensions 測試。"""

from __future__ import annotations

from exercises.part02.comprehensions import char_positions, evens_squared, flatten


def test_flatten() -> None:
    assert flatten([[1, 2], [3], [4, 5]]) == [1, 2, 3, 4, 5]


def test_flatten_empty() -> None:
    assert flatten([]) == []


def test_evens_squared() -> None:
    assert evens_squared(10) == [0, 4, 16, 36, 64]


def test_char_positions() -> None:
    assert char_positions("abca") == {"a": [0, 3], "b": [1], "c": [2]}
