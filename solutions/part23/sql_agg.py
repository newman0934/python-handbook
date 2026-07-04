"""Part 23 練習:SQL 聚合(承 02-sql-aggregation / 03-sql-joins)。"""

from __future__ import annotations

import sqlite3


def total_by_region(conn: sqlite3.Connection) -> dict[str, float]:
    """對 sales(region, amount) 表依 region 加總 amount,回傳 {region: total}。"""
    rows = conn.execute("SELECT region, SUM(amount) FROM sales GROUP BY region ORDER BY region")
    return {str(r[0]): float(r[1]) for r in rows}
