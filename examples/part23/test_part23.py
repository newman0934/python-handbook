"""Part 23 範例測試:工作流 / SQL 聚合·JOIN·window·CTE / pandas / EDA / 端到端。"""

from __future__ import annotations

import pandas as pd

from examples.part23.analysis import (
    aggregate_totals,
    city_revenue_pipeline,
    clean_records,
    customer_totals_left_join,
    eda_frame,
    iqr_outliers,
    left_merge_customers,
    make_join_db,
    make_sales_db,
    multi_agg,
    pct_in_region,
    pivot_sql,
    pivot_wide,
    rank_by_region_sql,
    region_totals_sql,
    sales_df,
    top_month_per_region_sql,
)


# ===== ch01 工作流 =====
def test_clean_drops_unparseable() -> None:
    rows = [
        {"region": "North", "amount": "100"},
        {"region": "north", "amount": ""},  # 缺值 → 丟
        {"region": "South", "amount": "abc"},  # 髒值 → 丟
    ]
    cleaned = clean_records(rows)
    assert len(cleaned) == 1
    assert cleaned[0]["region"] == "North"


def test_clean_normalizes_case() -> None:
    rows = [
        {"region": "North", "amount": "100"},
        {"region": "north", "amount": "200"},  # 大小寫應被標準化為同區
    ]
    totals = aggregate_totals(clean_records(rows))
    assert totals == {"North": 300.0}


# ===== ch02 SQL 聚合 =====
def test_region_totals() -> None:
    conn = make_sales_db()
    result = dict(region_totals_sql(conn))
    assert result["South"] == 2900.0
    assert result["North"] == 2700.0
    conn.close()


# ===== ch03 JOIN =====
def test_left_join_keeps_no_order_customer() -> None:
    conn = make_join_db()
    result = {row[0]: (row[1], row[2]) for row in customer_totals_left_join(conn)}
    assert result["Alice"] == (2, 800.0)  # 2 筆共 800
    assert result["Carol"] == (0, 0)  # 無訂單也保留,為 0
    conn.close()


# ===== ch04 window =====
def test_rank_by_region() -> None:
    conn = make_sales_db()
    ranks = rank_by_region_sql(conn)
    # 每區排名第 1 的月營收最高:North 2024-01 = A1000+B500 = 1500 > 2024-02 的 1200
    north_top = next(r for r in ranks if r[0] == "North" and r[2] == 1)
    assert north_top[1] == "2024-01"
    conn.close()


# ===== ch05 CTE / 樞紐 =====
def test_top_month_per_region() -> None:
    conn = make_sales_db()
    result = dict(top_month_per_region_sql(conn))
    assert result["North"] == "2024-01"  # 1500 > 1200
    assert result["South"] == "2024-02"  # 1500 > 800
    conn.close()


def test_case_pivot() -> None:
    conn = make_sales_db()
    result = {row[0]: (row[1], row[2]) for row in pivot_sql(conn)}
    assert result["North"] == (2200.0, 500.0)  # A=1000+1200, B=500
    conn.close()


# ===== ch06 pandas groupby =====
def test_multi_agg() -> None:
    agg = multi_agg(sales_df()).set_index("region")
    assert agg.loc["South", "total"] == 3000
    assert agg.loc["North", "orders"] == 3


def test_transform_pct() -> None:
    df = sales_df()
    pct = pct_in_region(df)
    # 第一筆 North A 1200 / North 總 2400 = 50%
    assert pct.iloc[0] == 50.0
    assert len(pct) == len(df)  # transform 保形


# ===== ch07 merge / reshape =====
def test_left_merge_has_nan_for_unmatched() -> None:
    merged = left_merge_customers()
    carol = merged[merged["name"] == "Carol"]
    assert carol["amount"].isna().all()  # Carol 無訂單


def test_pivot_wide() -> None:
    wide = pivot_wide(sales_df())
    assert wide.loc["North", "A"] == 1600  # 1200 + 400
    assert wide.loc["South", "B"] == 600


# ===== ch08 EDA =====
def test_iqr_detects_outlier() -> None:
    df = eda_frame()
    outliers = iqr_outliers(df["age"].dropna())
    assert outliers == [200.0]  # 200 是離群


def test_describe_missing_count() -> None:
    df = eda_frame()
    assert df["age"].isna().sum() == 1
    assert df["age"].describe()["count"] == 9  # describe 跳過缺值


# ===== ch09 端到端 =====
def test_city_pipeline() -> None:
    df = city_revenue_pipeline()
    assert df.iloc[0]["city"] == "Taipei"  # Taipei 營收最高(800)
    assert abs(df["pct"].sum() - 100.0) < 0.5  # 佔比加總約 100%


def test_pipeline_returns_dataframe() -> None:
    assert isinstance(city_revenue_pipeline(), pd.DataFrame)
