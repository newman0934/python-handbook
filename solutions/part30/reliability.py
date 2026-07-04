"""Part 30 練習:指數退避(承 03-reliability)。"""

from __future__ import annotations


def backoff_delays(attempts: int, base: float = 1.0, cap: float = 60.0) -> list[float]:
    """回傳指數退避延遲序列:base * 2^i,上限 cap。attempts<=0 回 []。"""
    return [min(cap, base * (2**i)) for i in range(max(0, attempts))]
