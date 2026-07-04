"""Part 11 練習:datetime(承 03-datetime)。"""

from __future__ import annotations

from datetime import date


def days_between(a: date, b: date) -> int:
    """回傳兩個日期相差的天數(絕對值)。"""
    return abs((b - a).days)


def is_weekend(d: date) -> bool:
    """判斷是否為週末(週六=5、週日=6)。"""
    return d.weekday() >= 5
