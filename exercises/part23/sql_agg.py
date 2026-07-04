"""Part 23 練習:SQL 聚合(承 02-sql-aggregation / 03-sql-joins)。

實作 total_by_region:對 sales(region, amount) 用 GROUP BY 依 region 加總,回傳 dict。
"""

from __future__ import annotations

import sqlite3


def total_by_region(conn: sqlite3.Connection) -> dict[str, float]:
    """對 sales(region, amount) 表依 region 加總 amount,回傳 {region: total}。"""
    raise NotImplementedError("實作我!")
