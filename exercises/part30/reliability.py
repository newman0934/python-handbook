"""Part 30 練習:指數退避(承 03-reliability)。

實作 backoff_delays:第 i 次(0-based)延遲 base*2^i,但不超過 cap。
例:backoff_delays(5) -> [1, 2, 4, 8, 16]。這是重試上游暫時性失敗的標準策略。
"""

from __future__ import annotations


def backoff_delays(attempts: int, base: float = 1.0, cap: float = 60.0) -> list[float]:
    """回傳指數退避延遲序列:base * 2^i,上限 cap。attempts<=0 回 []。"""
    raise NotImplementedError("實作我!")
