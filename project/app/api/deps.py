"""API 依賴:從 app.state 取出 TaskService(FastAPI 依賴注入)。"""

from __future__ import annotations

from fastapi import Request

from project.app.service.task_service import TaskService


def get_service(request: Request) -> TaskService:
    service = request.app.state.task_service
    assert isinstance(service, TaskService)
    return service
