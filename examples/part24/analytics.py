"""Part 24 統計分析與商業洞察範例:描述統計 / 相關與辛普森 / 假設檢定 /
A/B / 時間序列 / 商業指標 / 視覺化選擇 / 說故事 / 端到端報告。

統計用 stdlib statistics + NormalDist;時間序列/指標用 pandas。
"""

from __future__ import annotations

import math
import statistics as st
from dataclasses import dataclass
from statistics import NormalDist

import pandas as pd


# ===== ch01 描述統計 =====
def summary(data: list[float]) -> dict[str, float]:
    return {
        "mean": round(st.mean(data), 1),
        "median": st.median(data),
        "stdev": round(st.stdev(data), 1),
    }


def cv_percent(data: list[float]) -> float:
    return round(st.stdev(data) / st.mean(data) * 100, 1)


# ===== ch02 相關與辛普森 =====
def correlation(xs: list[float], ys: list[float]) -> float:
    return round(st.correlation(xs, ys), 3)


def simpson_reversal(groups: dict[str, dict[str, tuple[int, int]]]) -> dict[str, bool]:
    """回各組 A 是否較高 + 整體 A 是否較高,展示辛普森反轉。"""
    per_group_a_higher = []
    a_s = a_n = b_s = b_n = 0
    for data in groups.values():
        a_success, a_total = data["A"]
        b_success, b_total = data["B"]
        per_group_a_higher.append(a_success / a_total > b_success / b_total)
        a_s, a_n = a_s + a_success, a_n + a_total
        b_s, b_n = b_s + b_success, b_n + b_total
    return {
        "all_groups_a_higher": all(per_group_a_higher),
        "overall_a_higher": a_s / a_n > b_s / b_n,
    }


# ===== ch03-04 假設檢定 / A/B =====
def two_proportion_z_test(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float]:
    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se
    return z, 2 * (1 - NormalDist().cdf(abs(z)))


def sample_size_per_group(
    baseline: float, mde: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    p1, p2 = baseline, baseline + mde
    z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
    z_beta = NormalDist().inv_cdf(power)
    p_bar = (p1 + p2) / 2
    numerator = (
        z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
        + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    return math.ceil(numerator / mde**2)


# ===== ch05 時間序列 =====
def cagr(start: float, end: float, periods: int) -> float:
    return float((end / start) ** (1 / periods) - 1)


def moving_average(values: list[float], window: int) -> list[float]:
    s = pd.Series(values)
    return s.rolling(window).mean().dropna().round(1).tolist()


# ===== ch06 商業指標 =====
def funnel_conversions(stages: list[tuple[str, int]]) -> list[float]:
    """各階段相對前一階段的轉換率。"""
    return [round(stages[i][1] / stages[i - 1][1], 3) for i in range(1, len(stages))]


def largest_dropoff(stages: list[tuple[str, int]]) -> tuple[str, int]:
    drops = [(stages[i][0], stages[i - 1][1] - stages[i][1]) for i in range(1, len(stages))]
    return max(drops, key=lambda x: x[1])


def cohort_retention_pct(m0: int, later: list[int]) -> list[float]:
    return [round(v / m0 * 100, 1) for v in later]


# ===== ch07 視覺化 =====
def recommend_chart(purpose: str, data_type: str) -> str:
    rules = {
        ("comparison", "categorical"): "bar",
        ("trend", "time_series"): "line",
        ("distribution", "numeric"): "histogram",
        ("relationship", "two_numeric"): "scatter",
    }
    return rules.get((purpose, data_type), "unknown")


def bar_baseline_exaggeration(y_min: float, values: list[float]) -> float:
    """長條圖基線非 0 的誇大倍數(1.0=誠實)。"""
    if y_min <= 0:
        return 1.0
    v_small, v_large = min(values), max(values)
    visual_ratio = (v_large - y_min) / (v_small - y_min)
    return round(visual_ratio / (v_large / v_small), 2)


# ===== ch08-09 說故事 / 報告 =====
@dataclass
class Insight:
    finding: str
    so_what: str
    action: str


def pyramid_summary(headline: str, insights: list[Insight]) -> list[str]:
    """回報告的行清單:結論先行 + 各洞察。"""
    lines = [headline]
    for ins in insights:
        lines.append(f"{ins.finding} | {ins.so_what} | {ins.action}")
    return lines


def tailor_for(audience: str, insight: Insight) -> str:
    if audience == "executive":
        return f"{insight.so_what} → {insight.action}"
    return f"{insight.finding}(意涵:{insight.so_what})"
