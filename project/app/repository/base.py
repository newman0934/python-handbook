"""資料存取層介面:Repository 模式 + Protocol(承 Part 16 04-repository-pattern)。

業務層只依賴這個介面,不知道背後是記憶體、SQL 還是別的——可替換、可測。
"""

from __future__ import annotations

from typing import Protocol

from project.app.models.task import Task


class TaskRepository(Protocol):
    def add(self, title: str, description: str) -> Task: ...
    def get(self, task_id: int) -> Task | None: ...
    def list_all(self) -> list[Task]: ...
    def update(self, task: Task) -> Task: ...
    def delete(self, task_id: int) -> bool: ...
