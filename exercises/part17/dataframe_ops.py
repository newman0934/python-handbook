"""Part 17 練習:pandas 分組彙總(承 pandas 章)。

實作 total_by_category(依 category 分組加總 amount,回傳 dict)與
top_category(加總最高的類別)。提示:df.groupby(...)[...].sum()。
"""

from __future__ import annotations

import pandas as pd


def total_by_category(df: pd.DataFrame) -> dict[str, float]:
    """依 category 分組加總 amount,回傳 {category: total}。"""
    raise NotImplementedError("實作我!")


def top_category(df: pd.DataFrame) -> str:
    """回傳 amount 加總最高的 category。"""
    raise NotImplementedError("實作我!")
