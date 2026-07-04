"""Part 15 實戰篇 ch22/ch23 可執行範例。

- ch22 PostgreSQL 專屬功能:用 stdlib sqlite3 示範共通功能
  (JSON 查詢、ON CONFLICT UPSERT、RETURNING、部分索引)
- ch23 多資料庫語法對照:跨方言語法查詢器

全部純標準庫、可離線測試(sqlite3 為 Python 內建)。
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

# ---------------------------------------------------------------------------
# ch22 PostgreSQL 專屬功能(用 sqlite3 示範共通觀念)
# ---------------------------------------------------------------------------


def new_orders_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            total REAL NOT NULL,
            status TEXT NOT NULL,
            meta TEXT
        )
        """
    )
    return conn


def upsert_order(
    conn: sqlite3.Connection, oid: int, total: float, status: str, meta: dict[str, Any]
) -> None:
    """UPSERT:插入,主鍵衝突則更新(對應 PostgreSQL ON CONFLICT)。"""
    conn.execute(
        """INSERT INTO orders (id, total, status, meta) VALUES (?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET total=excluded.total,
                                         status=excluded.status,
                                         meta=excluded.meta""",
        (oid, total, status, json.dumps(meta)),
    )


def find_by_json_field(conn: sqlite3.Connection, field: str, value: str) -> list[tuple[Any, ...]]:
    """JSON 欄位查詢(對應 PostgreSQL meta ->> field)。"""
    rows: list[tuple[Any, ...]] = conn.execute(
        f"SELECT id FROM orders WHERE json_extract(meta, '$.{field}') = ?",
        (value,),
    ).fetchall()
    return rows


def insert_returning(conn: sqlite3.Connection, oid: int, total: float) -> tuple[Any, ...]:
    """RETURNING:寫入同時拿回結果。"""
    cur = conn.execute(
        "INSERT INTO orders (id, total, status, meta) "
        "VALUES (?, ?, 'active', '{}') RETURNING id, total",
        (oid, total),
    )
    return tuple(cur.fetchone())


def uses_partial_index(conn: sqlite3.Connection) -> bool:
    """建部分索引後,查詢是否走該索引(用 EXPLAIN QUERY PLAN 檢查)。"""
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_active_total ON orders(total) WHERE status='active'"
    )
    plan = conn.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM orders WHERE status='active' AND total>90"
    ).fetchall()
    return any("idx_active_total" in str(r) for r in plan)


# ---------------------------------------------------------------------------
# ch23 多資料庫語法對照
# ---------------------------------------------------------------------------

DIALECT: dict[str, dict[str, str]] = {
    "auto_increment": {
        "postgresql": "id SERIAL PRIMARY KEY",
        "mysql": "id INT AUTO_INCREMENT PRIMARY KEY",
        "sqlite": "id INTEGER PRIMARY KEY AUTOINCREMENT",
    },
    "paginate": {
        "postgresql": "LIMIT 10 OFFSET 20",
        "mysql": "LIMIT 20, 10",
        "sqlite": "LIMIT 10 OFFSET 20",
    },
    "upsert": {
        "postgresql": "INSERT ... ON CONFLICT (id) DO UPDATE SET ...",
        "mysql": "INSERT ... ON DUPLICATE KEY UPDATE ...",
        "sqlite": "INSERT ... ON CONFLICT (id) DO UPDATE SET ...",
    },
    "string_concat": {
        "postgresql": "a || b",
        "mysql": "CONCAT(a, b)",
        "sqlite": "a || b",
    },
    "returning": {
        "postgresql": "INSERT ... RETURNING id",
        "mysql": "INSERT ...; SELECT LAST_INSERT_ID()",
        "sqlite": "INSERT ... RETURNING id",
    },
}


def syntax_for(operation: str, dialect: str) -> str:
    if operation not in DIALECT:
        raise KeyError(f"未知操作: {operation}")
    variants = DIALECT[operation]
    if dialect not in variants:
        raise KeyError(f"未知方言: {dialect}")
    return variants[dialect]


def differs_across(operation: str) -> bool:
    """該操作是否跨方言有差異(值不全相同)。"""
    return len(set(DIALECT[operation].values())) > 1


def main() -> None:  # pragma: no cover
    conn = new_orders_db()
    upsert_order(conn, 1, 100.0, "active", {"coupon": "X"})
    upsert_order(conn, 1, 120.0, "active", {"coupon": "X"})
    print("ch22 UPSERT total:", conn.execute("SELECT total FROM orders WHERE id=1").fetchone())
    print("ch22 JSON 查詢:", find_by_json_field(conn, "coupon", "X"))
    print("ch22 RETURNING:", insert_returning(conn, 3, 88.0))
    print("ch22 部分索引:", uses_partial_index(conn))
    print("ch23 MySQL upsert:", syntax_for("upsert", "mysql"))


if __name__ == "__main__":
    main()
