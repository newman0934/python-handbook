"""Part 24 練習:描述統計與成長率(承 統計 / 商業洞察)。

實作 describe(mean/median/pstdev)與 growth_rate((new-old)/old,old=0 丟 ValueError)。
提示:用 statistics 模組。
"""

from __future__ import annotations


def describe(data: list[float]) -> dict[str, float]:
    """回傳 {mean, median, stdev}(母體標準差 pstdev)。"""
    raise NotImplementedError("實作我!")


def growth_rate(old: float, new: float) -> float:
    """成長率 (new - old) / old;old 為 0 丟 ValueError。"""
    raise NotImplementedError("實作我!")
