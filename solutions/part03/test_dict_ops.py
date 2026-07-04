"""Part 3 dict_ops 測試。"""

from __future__ import annotations

from solutions.part03.dict_ops import group_by_length, invert


def test_group_by_length() -> None:
    assert group_by_length(["a", "bb", "cc", "ddd"]) == {
        1: ["a"],
        2: ["bb", "cc"],
        3: ["ddd"],
    }


def test_group_empty() -> None:
    assert group_by_length([]) == {}


def test_invert() -> None:
    assert invert({"a": 1, "b": 2}) == {1: "a", 2: "b"}
