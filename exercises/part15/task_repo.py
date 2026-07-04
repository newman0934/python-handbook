"""Part 15 練習:sqlite3 CRUD(承 11-db-api / 12-sqlite3)。

用 stdlib sqlite3 實作 init_db / add_task(回傳 id)/ complete_task /
list_open_titles。務必用『參數化查詢』(? 佔位),不可字串拼接。
"""

from __future__ import annotations

import sqlite3


def init_db(conn: sqlite3.Connection) -> None:
    """建立 tasks 表(id 自增主鍵、title、done 預設 0)。"""
    raise NotImplementedError("實作我!")


def add_task(conn: sqlite3.Connection, title: str) -> int:
    """新增任務,回傳新的 id(參數化查詢)。"""
    raise NotImplementedError("實作我!")


def complete_task(conn: sqlite3.Connection, task_id: int) -> None:
    """把指定任務標記為完成。"""
    raise NotImplementedError("實作我!")


def list_open_titles(conn: sqlite3.Connection) -> list[str]:
    """回傳所有未完成任務的標題(依 id 排序)。"""
    raise NotImplementedError("實作我!")
