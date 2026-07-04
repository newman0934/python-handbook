"""業務邏輯層:協調 repository、施加規則、拋領域例外(承 Part 16 分層架構)。"""

from __future__ import annotations

from project.app.exceptions import TaskNotFoundError
from project.app.models.task import Task, TaskCreate, TaskUpdate
from project.app.repository.base import TaskRepository


class TaskService:
    """依賴注入:建構時接收 TaskRepository 介面(不自己建立)。"""

    def __init__(self, repository: TaskRepository) -> None:
        self._repo = repository

    def create(self, data: TaskCreate) -> Task:
        return self._repo.add(data.title, data.description)

    def get(self, task_id: int) -> Task:
        task = self._repo.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def list(self) -> list[Task]:
        return self._repo.list_all()

    def update(self, task_id: int, data: TaskUpdate) -> Task:
        task = self.get(task_id)
        changes = data.model_dump(exclude_none=True)
        return self._repo.update(task.model_copy(update=changes))

    def complete(self, task_id: int) -> Task:
        task = self.get(task_id)
        return self._repo.update(task.model_copy(update={"done": True}))

    def delete(self, task_id: int) -> None:
        if not self._repo.delete(task_id):
            raise TaskNotFoundError(task_id)
