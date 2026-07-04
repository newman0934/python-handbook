"""Part 24 練習:描述統計與成長率(承 統計 / 商業洞察)。"""

from __future__ import annotations

import statistics


def describe(data: list[float]) -> dict[str, float]:
    """回傳 {mean, median, stdev}(母體標準差 pstdev)。"""
    return {
        "mean": statistics.mean(data),
        "median": statistics.median(data),
        "stdev": statistics.pstdev(data),
    }


def growth_rate(old: float, new: float) -> float:
    """成長率 (new - old) / old;old 為 0 丟 ValueError。"""
    if old == 0:
        raise ValueError("old 不可為 0")
    return (new - old) / old
