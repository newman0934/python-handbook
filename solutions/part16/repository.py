"""Part 16 練習:Repository 模式 + Protocol(承 04-repository-pattern)。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Task:
    id: int
    title: str
    done: bool = False


class TaskRepository(Protocol):
    """資料存取介面(結構型定型):任何具備這些方法的物件都算 repo。"""

    def add(self, title: str) -> Task: ...
    def get(self, task_id: int) -> Task | None: ...
    def list_all(self) -> list[Task]: ...


class InMemoryTaskRepository:
    """以 dict 實作的記憶體 repo(測試/範例用,不需真的 DB)。"""

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id = 1

    def add(self, title: str) -> Task:
        task = Task(self._next_id, title)
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    def get(self, task_id: int) -> Task | None:
        return self._tasks.get(task_id)

    def list_all(self) -> list[Task]:
        return list(self._tasks.values())


def count_done(repo: TaskRepository) -> int:
    """示範:依賴介面而非具體實作,計算已完成任務數。"""
    return sum(1 for t in repo.list_all() if t.done)
