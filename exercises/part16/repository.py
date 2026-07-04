"""Part 16 練習:Repository 模式 + Protocol(承 04-repository-pattern)。

實作 InMemoryTaskRepository(以 dict 儲存,add 自動遞增 id)與 count_done
(接受任何符合 TaskRepository 介面的物件)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Task:
    id: int
    title: str
    done: bool = False


class TaskRepository(Protocol):
    def add(self, title: str) -> Task: ...
    def get(self, task_id: int) -> Task | None: ...
    def list_all(self) -> list[Task]: ...


class InMemoryTaskRepository:
    def __init__(self) -> None:
        raise NotImplementedError("實作我!")

    def add(self, title: str) -> Task:
        raise NotImplementedError("實作我!")

    def get(self, task_id: int) -> Task | None:
        raise NotImplementedError("實作我!")

    def list_all(self) -> list[Task]:
        raise NotImplementedError("實作我!")


def count_done(repo: TaskRepository) -> int:
    """依賴介面而非具體實作,計算已完成任務數。"""
    raise NotImplementedError("實作我!")
