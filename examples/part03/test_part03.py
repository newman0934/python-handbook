"""Part 3 範例的驗證測試。

執行：pytest examples/part03
"""

import pytest

from examples.part03.data_structures import (
    Color,
    build_matrix,
    dedupe_keep_order,
    deep_is_isolated,
    grade,
    group_by_length,
    k_largest,
    shallow_leaks_inner,
    sort_by_second,
    word_count,
)


def test_build_matrix_rows_are_independent() -> None:
    m = build_matrix(2, 2)
    m[0][0] = 1
    assert m == [[1, 0], [0, 0]]  # 只有第一列變，證明沒有別名陷阱


def test_dedupe_keeps_order() -> None:
    assert dedupe_keep_order([3, 1, 2, 2, 3, 1]) == [3, 1, 2]


def test_group_by_length() -> None:
    assert group_by_length(["hi", "ok", "hello", "a"]) == {
        2: ["hi", "ok"],
        5: ["hello"],
        1: ["a"],
    }


def test_word_count() -> None:
    assert word_count("the cat the dog the") == {"the": 3, "cat": 1, "dog": 1}


def test_shallow_copy_leaks_inner() -> None:
    assert shallow_leaks_inner() == [[1, 2, 99], [3, 4]]


def test_deep_copy_is_isolated() -> None:
    assert deep_is_isolated() == [[1, 2], [3, 4]]


def test_frozen_dataclass_is_hashable_and_dedupes() -> None:
    red1 = Color(255, 0, 0)
    red2 = Color(255, 0, 0)
    assert red1 == red2
    assert hash(red1) == hash(red2)
    assert len({red1, red2, Color(0, 255, 0)}) == 2


def test_sort_by_second_is_stable() -> None:
    # 25 分同分者維持原相對順序（穩定排序）
    assert sort_by_second([("Bob", 25), ("Alice", 30), ("Cara", 25)]) == [
        ("Bob", 25),
        ("Cara", 25),
        ("Alice", 30),
    ]


@pytest.mark.parametrize(
    ("score", "expected"),
    [(55, "F"), (65, "D"), (72, "C"), (88, "B"), (95, "A"), (60, "D"), (90, "A")],
)
def test_grade(score: int, expected: str) -> None:
    assert grade(score) == expected


def test_k_largest() -> None:
    assert k_largest([5, 1, 8, 3, 9, 2], 3) == [9, 8, 5]
