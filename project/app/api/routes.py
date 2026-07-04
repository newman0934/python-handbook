"""路由層:把 HTTP 請求轉給 TaskService(承 Part 14 REST API)。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from project.app.api.deps import get_service
from project.app.models.task import Task, TaskCreate, TaskUpdate
from project.app.service.task_service import TaskService

# Annotated 依賴(現代 FastAPI 寫法,避免在預設值放函式呼叫)
ServiceDep = Annotated[TaskService, Depends(get_service)]

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
def list_tasks(service: ServiceDep) -> list[Task]:
    return service.list()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, service: ServiceDep) -> Task:
    return service.create(data)


@router.get("/{task_id}")
def get_task(task_id: int, service: ServiceDep) -> Task:
    return service.get(task_id)


@router.patch("/{task_id}")
def update_task(task_id: int, data: TaskUpdate, service: ServiceDep) -> Task:
    return service.update(task_id, data)


@router.post("/{task_id}/complete")
def complete_task(task_id: int, service: ServiceDep) -> Task:
    return service.complete(task_id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, service: ServiceDep) -> None:
    service.delete(task_id)
