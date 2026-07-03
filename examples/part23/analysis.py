"""Part 23 分析用 SQL 與資料整理範例:工作流 / SQL 聚合·JOIN·window·CTE /
pandas groupby·merge·pivot / EDA / 端到端。

SQL 用 stdlib sqlite3;資料整理用 pandas。
"""

from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd


# ===== ch01 分析工作流 =====
def clean_records(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """標準化 + 解析,丟棄無法解析的。"""
    cleaned: list[dict[str, object]] = []
    for row in rows:
        region = row["region"].strip().title()
        try:
            amount = float(row["amount"])
        except ValueError:
            continue
        cleaned.append({"region": region, "amount": amount})
    return cleaned


def aggregate_totals(rows: list[dict[str, object]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for row in rows:
        region = str(row["region"])
        totals[region] = totals.get(region, 0.0) + float(str(row["amount"]))
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


# ===== ch02-05 SQL =====
def make_sales_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE sales(month TEXT, region TEXT, product TEXT, amount REAL);
        INSERT INTO sales VALUES
          ('2024-01','North','A',1000),('2024-01','North','B',500),('2024-02','North','A',1200),
          ('2024-01','South','A',800),('2024-02','South','B',1500),('2024-02','South','A',600);
    """)
    return conn


def region_totals_sql(conn: sqlite3.Connection) -> list[tuple[str, float]]:
    """ch02 GROUP BY 聚合。"""
    return list(
        conn.execute("SELECT region, SUM(amount) FROM sales GROUP BY region ORDER BY 2 DESC")
    )


def rank_by_region_sql(conn: sqlite3.Connection) -> list[tuple[str, str, int]]:
    """ch04 window RANK。"""
    return list(
        conn.execute(
            "SELECT region, month, "
            "RANK() OVER (PARTITION BY region ORDER BY SUM(amount) DESC) AS rnk "
            "FROM sales GROUP BY region, month ORDER BY region, rnk"
        )
    )


def top_month_per_region_sql(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """ch05 CTE + window + 外層過濾:每區營收最高月。"""
    return list(
        conn.execute("""
            WITH ranked AS (
                SELECT region, month, SUM(amount) AS m_total,
                       RANK() OVER (PARTITION BY region ORDER BY SUM(amount) DESC) AS rnk
                FROM sales GROUP BY region, month
            )
            SELECT region, month FROM ranked WHERE rnk = 1 ORDER BY region
        """)
    )


def pivot_sql(conn: sqlite3.Connection) -> list[tuple[str, float, float]]:
    """ch05 CASE 樞紐。"""
    return list(
        conn.execute(
            "SELECT region, "
            "SUM(CASE WHEN product='A' THEN amount ELSE 0 END) AS a, "
            "SUM(CASE WHEN product='B' THEN amount ELSE 0 END) AS b "
            "FROM sales GROUP BY region ORDER BY region"
        )
    )


def make_join_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE customers(cid INTEGER, name TEXT, city TEXT);
        CREATE TABLE orders(oid INTEGER, cid INTEGER, amount REAL);
        INSERT INTO customers VALUES (1,'Alice','Taipei'),(2,'Bob','Tainan'),(3,'Carol','Taipei');
        INSERT INTO orders VALUES (101,1,500),(102,1,300),(103,2,800);
    """)  # Carol(3)無訂單
    return conn


def customer_totals_left_join(conn: sqlite3.Connection) -> list[tuple[str, int, float]]:
    """ch03 LEFT JOIN 保留無訂單客戶。"""
    return list(
        conn.execute(
            "SELECT c.name, COUNT(o.oid) AS n, COALESCE(SUM(o.amount),0) AS total "
            "FROM customers c LEFT JOIN orders o ON c.cid = o.cid "
            "GROUP BY c.cid ORDER BY total DESC"
        )
    )


# ===== ch06 pandas groupby =====
def sales_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "region": ["North", "North", "South", "South", "North", "South"],
            "product": ["A", "B", "A", "B", "A", "A"],
            "amount": [1200, 800, 1500, 600, 400, 900],
            "qty": [3, 2, 5, 1, 1, 3],
        }
    )


def multi_agg(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("region")
        .agg(total=("amount", "sum"), avg=("amount", "mean"), orders=("amount", "count"))
        .reset_index()
    )


def pct_in_region(df: pd.DataFrame) -> pd.Series:
    """ch06 transform 佔區內比例(保形)。"""
    region_total = df.groupby("region")["amount"].transform("sum")
    return (df["amount"] / region_total * 100).round(1)


# ===== ch07 merge / pivot / melt =====
def left_merge_customers() -> pd.DataFrame:
    customers = pd.DataFrame({"cid": [1, 2, 3], "name": ["Alice", "Bob", "Carol"]})
    orders = pd.DataFrame({"cid": [1, 1, 2], "amount": [500, 300, 800]})
    return customers.merge(orders, on="cid", how="left")


def pivot_wide(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(
        index="region", columns="product", values="amount", aggfunc="sum", fill_value=0
    )


# ===== ch08 EDA =====
def iqr_outliers(s: pd.Series) -> list[float]:
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return s[(s < lo) | (s > hi)].tolist()


def eda_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [25, 30, 35, 40, 45, 50, 200, np.nan, 28, 33],
            "income": [30, 45, 50, 60, 80, 90, 100, 55, None, 70],
        }
    )


# ===== ch09 端到端 =====
def city_revenue_pipeline() -> pd.DataFrame:
    """SQL JOIN + 聚合撈數 → pandas 算佔比(Taipei 明顯最高)。"""
    conn = sqlite3.connect(":memory:")
    conn.executescript("""
        CREATE TABLE customers(cid INTEGER, name TEXT, city TEXT);
        CREATE TABLE orders(oid INTEGER, cid INTEGER, amount REAL);
        INSERT INTO customers VALUES
          (1,'Alice','Taipei'),(2,'Bob','Tainan'),(3,'Carol','Taipei');
        INSERT INTO orders VALUES (101,1,500),(102,1,700),(103,2,800),(104,3,500);
    """)  # Taipei = Alice1200 + Carol500 = 1700 > Tainan 800
    df = pd.read_sql_query(
        "SELECT c.city, SUM(o.amount) AS revenue "
        "FROM orders o JOIN customers c ON o.cid = c.cid GROUP BY c.city",
        conn,
    )
    df["pct"] = (df["revenue"] / df["revenue"].sum() * 100).round(1)
    conn.close()
    return df.sort_values("revenue", ascending=False).reset_index(drop=True)
