"""Part 6 練習:例外處理與 EAFP(承 02-try-except / 09-eafp-vs-lbyl)。"""

from __future__ import annotations


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """a/b;除以 0 時回 default(不拋例外)。"""
    try:
        return a / b
    except ZeroDivisionError:
        return default


def parse_int_or(s: str, default: int) -> int:
    """把 s 轉 int;失敗回 default(EAFP)。"""
    try:
        return int(s)
    except ValueError:
        return default
