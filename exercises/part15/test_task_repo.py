"""Part 15 task_repo 測試。"""

from __future__ import annotations

import sqlite3

import pytest

from exercises.part15.task_repo import add_task, complete_task, init_db, list_open_titles


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    init_db(c)
    return c


def test_add_and_list(conn: sqlite3.Connection) -> None:
    add_task(conn, "buy milk")
    add_task(conn, "walk dog")
    assert list_open_titles(conn) == ["buy milk", "walk dog"]


def test_add_returns_incrementing_id(conn: sqlite3.Connection) -> None:
    assert add_task(conn, "a") == 1
    assert add_task(conn, "b") == 2


def test_complete_hides_from_open(conn: sqlite3.Connection) -> None:
    tid = add_task(conn, "task")
    add_task(conn, "other")
    complete_task(conn, tid)
    assert list_open_titles(conn) == ["other"]
