"""Part 16 repository 測試。"""

from __future__ import annotations

from exercises.part16.repository import InMemoryTaskRepository, count_done


def test_add_assigns_incrementing_id() -> None:
    repo = InMemoryTaskRepository()
    a = repo.add("first")
    b = repo.add("second")
    assert (a.id, b.id) == (1, 2)


def test_get() -> None:
    repo = InMemoryTaskRepository()
    t = repo.add("x")
    assert repo.get(t.id) == t
    assert repo.get(999) is None


def test_count_done() -> None:
    repo = InMemoryTaskRepository()
    repo.add("a")
    b = repo.add("b")
    b.done = True
    assert count_done(repo) == 1
