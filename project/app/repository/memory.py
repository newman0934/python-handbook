"""記憶體 Repository 實作(預設;測試/開發用,不需外部 DB)。"""

from __future__ import annotations

from project.app.models.task import Task


class InMemoryTaskRepository:
    """以 dict 儲存任務,id 自動遞增。實作 TaskRepository 介面。"""

    def __init__(self) -> None:
        self._tasks: dict[int, Task] = {}
        self._next_id = 1

    def add(self, title: str, description: str) -> Task:
        task = Task.new(self._next_id, title, description)
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    def get(self, task_id: int) -> Task | None:
        return self._tasks.get(task_id)

    def list_all(self) -> list[Task]:
        return list(self._tasks.values())

    def update(self, task: Task) -> Task:
        self._tasks[task.id] = task
        return task

    def delete(self, task_id: int) -> bool:
        return self._tasks.pop(task_id, None) is not None
