"""Part 15 練習:sqlite3 CRUD(承 11-db-api / 12-sqlite3)。"""

from __future__ import annotations

import sqlite3


def init_db(conn: sqlite3.Connection) -> None:
    """建立 tasks 表(id 自增主鍵、title、done 預設 0)。"""
    conn.execute(
        """CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )"""
    )


def add_task(conn: sqlite3.Connection, title: str) -> int:
    """新增任務,回傳新的 id(參數化查詢)。"""
    cur = conn.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
    new_id = cur.lastrowid
    assert new_id is not None
    return new_id


def complete_task(conn: sqlite3.Connection, task_id: int) -> None:
    """把指定任務標記為完成。"""
    conn.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))


def list_open_titles(conn: sqlite3.Connection) -> list[str]:
    """回傳所有未完成任務的標題(依 id 排序)。"""
    rows = conn.execute("SELECT title FROM tasks WHERE done = 0 ORDER BY id")
    return [row[0] for row in rows]
