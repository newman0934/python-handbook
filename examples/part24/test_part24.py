"""Part 24 範例測試:描述統計 / 相關辛普森 / 檢定 / A/B / 時間序列 /
商業指標 / 視覺化 / 說故事 / 報告。"""

from __future__ import annotations

import pytest

from examples.part24.analytics import (
    Insight,
    bar_baseline_exaggeration,
    cagr,
    cohort_retention_pct,
    correlation,
    cv_percent,
    funnel_conversions,
    largest_dropoff,
    moving_average,
    pyramid_summary,
    recommend_chart,
    sample_size_per_group,
    simpson_reversal,
    summary,
    tailor_for,
    two_proportion_z_test,
)


# ===== ch01 描述統計 =====
def test_mean_vs_median_skew() -> None:
    s = summary([10, 20, 30, 40, 500])  # 右偏
    assert s["mean"] == 120
    assert s["median"] == 30  # median 不被極端值拉走


def test_cv_relative_dispersion() -> None:
    stable = cv_percent([100, 110, 90, 105, 95])
    volatile = cv_percent([10, 50, 30, 70, 20])
    assert volatile > stable  # 波動組相對離散更大


# ===== ch02 相關與辛普森 =====
def test_high_correlation() -> None:
    r = correlation([10, 20, 30, 40, 50], [2, 4, 5, 8, 10])
    assert r > 0.9


def test_simpson_paradox() -> None:
    groups = {
        "輕症": {"A": (81, 87), "B": (234, 270)},
        "重症": {"A": (192, 263), "B": (55, 80)},
    }
    result = simpson_reversal(groups)
    assert result["all_groups_a_higher"] is True  # 每組 A 較高
    assert result["overall_a_higher"] is False  # 但整體 B 較高(反轉)


# ===== ch03-04 檢定 / A/B =====
def test_z_test_significant() -> None:
    z, p = two_proportion_z_test(260, 2000, 200, 2000)
    assert p < 0.05  # 大樣本 13% vs 10% 顯著


def test_z_test_small_sample_not_significant() -> None:
    _, p = two_proportion_z_test(13, 100, 10, 100)
    assert p > 0.05  # 相同效果但小樣本 → 不顯著


def test_sample_size() -> None:
    n = sample_size_per_group(baseline=0.10, mde=0.02)
    assert 3000 < n < 4500  # 業界標準量級


def test_smaller_mde_needs_more_samples() -> None:
    n_big = sample_size_per_group(0.10, 0.05)
    n_small = sample_size_per_group(0.10, 0.01)
    assert n_small > n_big  # MDE 越小需要越多樣本


# ===== ch05 時間序列 =====
def test_cagr() -> None:
    # 100 → 200 經 2 期,CAGR ≈ 41.4%
    assert cagr(100, 200, 2) == pytest.approx(0.4142, abs=0.001)


def test_moving_average_smooths() -> None:
    ma = moving_average([10, 20, 30, 40, 50], window=3)
    assert ma == [20.0, 30.0, 40.0]  # 平滑後為中間值


# ===== ch06 商業指標 =====
def test_funnel_conversions() -> None:
    convs = funnel_conversions([("造訪", 1000), ("註冊", 400), ("下單", 100)])
    assert convs == [0.4, 0.25]


def test_largest_dropoff() -> None:
    stage, lost = largest_dropoff([("造訪", 10000), ("註冊", 4000), ("下單", 3000)])
    assert stage == "註冊"  # 造訪→註冊流失 6000 最多
    assert lost == 6000


def test_cohort_retention() -> None:
    assert cohort_retention_pct(1000, [400, 250, 180]) == [40.0, 25.0, 18.0]


# ===== ch07 視覺化 =====
def test_recommend_chart() -> None:
    assert recommend_chart("trend", "time_series") == "line"
    assert recommend_chart("comparison", "categorical") == "bar"


def test_baseline_exaggeration() -> None:
    assert bar_baseline_exaggeration(0, [100, 102]) == 1.0  # 基線 0 誠實
    assert bar_baseline_exaggeration(95, [100, 102]) > 1.3  # 截斷誇大


# ===== ch08-09 說故事 / 報告 =====
def test_pyramid_starts_with_headline() -> None:
    insights = [Insight("發現X", "意涵Y", "行動Z")]
    lines = pyramid_summary("結論在最前", insights)
    assert lines[0] == "結論在最前"  # 結論先行


def test_tailor_for_audience() -> None:
    ins = Insight("轉換 15%", "損失營收", "簡化流程")
    exec_msg = tailor_for("executive", ins)
    analyst_msg = tailor_for("analyst", ins)
    assert "簡化流程" in exec_msg  # 高管要行動
    assert "轉換 15%" in analyst_msg  # 分析師要細節
