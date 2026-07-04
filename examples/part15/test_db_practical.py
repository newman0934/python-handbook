"""Part 15 實戰篇 ch22/ch23 範例測試。"""

from __future__ import annotations

import sqlite3

import pytest

from examples.part15.db_practical import (
    DIALECT,
    differs_across,
    find_by_json_field,
    insert_returning,
    new_orders_db,
    syntax_for,
    upsert_order,
    uses_partial_index,
)

# ---- ch22 PostgreSQL 功能(sqlite 示範) ----


def test_upsert_inserts_then_updates() -> None:
    conn = new_orders_db()
    upsert_order(conn, 1, 100.0, "active", {"coupon": "X"})
    upsert_order(conn, 1, 120.0, "active", {"coupon": "X"})  # 衝突→更新
    total = conn.execute("SELECT total FROM orders WHERE id=1").fetchone()[0]
    assert total == 120.0
    # 只有一列(是更新不是新增)
    assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 1


def test_upsert_accumulates() -> None:
    conn = sqlite_kv()
    for _ in range(3):
        conn.execute(
            "INSERT INTO kv (k, hits) VALUES ('a', 1) ON CONFLICT(k) DO UPDATE SET hits = hits + 1"
        )
    assert conn.execute("SELECT hits FROM kv WHERE k='a'").fetchone()[0] == 3


def sqlite_kv() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE kv (k TEXT PRIMARY KEY, hits INT)")
    return conn


def test_json_field_query() -> None:
    conn = new_orders_db()
    upsert_order(conn, 1, 100.0, "active", {"coupon": "X"})
    upsert_order(conn, 2, 50.0, "archived", {"tags": ["normal"]})
    assert find_by_json_field(conn, "coupon", "X") == [(1,)]
    assert find_by_json_field(conn, "coupon", "Z") == []


def test_returning_gives_written_row() -> None:
    conn = new_orders_db()
    assert insert_returning(conn, 3, 88.0) == (3, 88.0)


def test_partial_index_used() -> None:
    conn = new_orders_db()
    upsert_order(conn, 1, 100.0, "active", {})
    assert uses_partial_index(conn) is True


# ---- ch23 方言對照 ----


@pytest.mark.parametrize(
    "op, dialect, expected",
    [
        ("upsert", "postgresql", "INSERT ... ON CONFLICT (id) DO UPDATE SET ..."),
        ("upsert", "mysql", "INSERT ... ON DUPLICATE KEY UPDATE ..."),
        ("auto_increment", "mysql", "id INT AUTO_INCREMENT PRIMARY KEY"),
        ("string_concat", "mysql", "CONCAT(a, b)"),
    ],
)
def test_syntax_for(op: str, dialect: str, expected: str) -> None:
    assert syntax_for(op, dialect) == expected


def test_postgres_and_sqlite_share_upsert_syntax() -> None:
    # PostgreSQL 與 SQLite 的 UPSERT/字串串接方言相同,MySQL 不同
    assert syntax_for("upsert", "postgresql") == syntax_for("upsert", "sqlite")
    assert syntax_for("string_concat", "postgresql") == syntax_for("string_concat", "sqlite")
    assert syntax_for("upsert", "mysql") != syntax_for("upsert", "postgresql")


def test_syntax_for_unknown_raises() -> None:
    with pytest.raises(KeyError):
        syntax_for("nonexistent", "postgresql")
    with pytest.raises(KeyError):
        syntax_for("upsert", "oracle")


def test_dialect_hotspots_differ() -> None:
    # 這些操作都是「方言熱區」,跨方言有差異
    for op in ("auto_increment", "paginate", "upsert", "string_concat"):
        assert differs_across(op) is True


def test_dialect_table_complete() -> None:
    # 每個操作都涵蓋三大方言
    for variants in DIALECT.values():
        assert {"postgresql", "mysql", "sqlite"} <= set(variants)
