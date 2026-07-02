"""Part 5 範例的驗證測試。

執行：pytest examples/part05
"""

from examples.part05.typing_examples import (
    Box,
    FluentList,
    Student,
    add,
    classify,
    first,
    parse,
    report,
    safe_upper,
    sum_if_ints,
    to_grade,
    total,
)


def test_generic_first_preserves_value() -> None:
    assert first([1, 2, 3]) == 1
    assert first(["a", "b"]) == "a"


def test_total_accepts_iterable() -> None:
    assert total([1, 2, 3]) == 6
    assert total((10, 20)) == 30
    assert total(x for x in [1, 2, 3]) == 6


def test_generic_box() -> None:
    assert Box(42).get() == 42
    assert Box("hi").get() == "hi"


def test_optional_narrowing() -> None:
    assert safe_upper(None) == ""
    assert safe_upper("ok") == "OK"
    assert classify(None) == "空"
    assert classify(5) == "整數5"
    assert classify("hi") == "字串hi"


def test_typeddict_report() -> None:
    s: Student = {"name": "Alice", "score": 92}
    assert report(s) == "Alice: A"


def test_to_grade() -> None:
    assert [to_grade(n) for n in (95, 85, 75, 65, 55)] == ["A", "B", "C", "D", "F"]


def test_overload_returns_by_input() -> None:
    assert parse("  hi ") == "hi"
    assert parse(3) == [0, 1, 2]


def test_typeguard() -> None:
    assert sum_if_ints([1, 2, 3]) == 6
    assert sum_if_ints([1, "x"]) == 0


def test_paramspec_decorator() -> None:
    assert add(2, 3) == [5, 5]


def test_self_chaining() -> None:
    assert FluentList().add(1).add(2).add(3).build() == [1, 2, 3]
