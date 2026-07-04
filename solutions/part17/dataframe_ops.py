"""Part 17 練習:pandas 分組彙總(承 pandas 章)。"""

from __future__ import annotations

import pandas as pd


def total_by_category(df: pd.DataFrame) -> dict[str, float]:
    """依 category 分組加總 amount,回傳 {category: total}。"""
    grouped = df.groupby("category")["amount"].sum()
    return {str(k): float(v) for k, v in grouped.items()}


def top_category(df: pd.DataFrame) -> str:
    """回傳 amount 加總最高的 category。"""
    totals = total_by_category(df)
    return max(totals, key=lambda k: totals[k])
