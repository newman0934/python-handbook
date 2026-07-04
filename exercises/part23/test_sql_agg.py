"""Part 23 sql_agg 測試。"""

from __future__ import annotations

import sqlite3

import pytest

from exercises.part23.sql_agg import total_by_region


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE sales (region TEXT, amount REAL)")
    c.executemany(
        "INSERT INTO sales VALUES (?, ?)",
        [("north", 100.0), ("south", 50.0), ("north", 20.0)],
    )
    return c


def test_total_by_region(conn: sqlite3.Connection) -> None:
    assert total_by_region(conn) == {"north": 120.0, "south": 50.0}
