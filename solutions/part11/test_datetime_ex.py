"""Part 11 datetime_ex 測試。"""

from __future__ import annotations

from datetime import date

from solutions.part11.datetime_ex import days_between, is_weekend


def test_days_between() -> None:
    assert days_between(date(2024, 1, 1), date(2024, 1, 11)) == 10


def test_days_between_order_independent() -> None:
    assert days_between(date(2024, 3, 1), date(2024, 1, 1)) == 60  # 2024 閏年


def test_is_weekend() -> None:
    assert is_weekend(date(2024, 6, 8)) is True  # 週六
    assert is_weekend(date(2024, 6, 9)) is True  # 週日
    assert is_weekend(date(2024, 6, 10)) is False  # 週一
