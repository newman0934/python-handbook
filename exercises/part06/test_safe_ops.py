"""Part 6 safe_ops 測試。"""

from __future__ import annotations

from exercises.part06.safe_ops import parse_int_or, safe_divide


def test_safe_divide() -> None:
    assert safe_divide(10, 2) == 5


def test_safe_divide_by_zero() -> None:
    assert safe_divide(10, 0, default=-1) == -1


def test_parse_int_ok() -> None:
    assert parse_int_or("42", 0) == 42


def test_parse_int_fallback() -> None:
    assert parse_int_or("abc", -1) == -1
