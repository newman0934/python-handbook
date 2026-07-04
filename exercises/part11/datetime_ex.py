"""Part 11 練習:datetime(承 03-datetime)。

實作 days_between(兩日期相差天數,絕對值)與 is_weekend(週六/週日為 True)。
"""

from __future__ import annotations

from datetime import date


def days_between(a: date, b: date) -> int:
    """回傳兩個日期相差的天數(絕對值)。"""
    raise NotImplementedError("實作我!")


def is_weekend(d: date) -> bool:
    """判斷是否為週末(週六=5、週日=6)。"""
    raise NotImplementedError("實作我!")
