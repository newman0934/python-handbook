"""進入點:app factory 組裝各層(啟動:uvicorn project.app.main:app)。"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from project.app.api.routes import router
from project.app.exceptions import TaskNotFoundError
from project.app.repository.base import TaskRepository
from project.app.repository.memory import InMemoryTaskRepository
from project.app.service.task_service import TaskService


def create_app(repository: TaskRepository | None = None) -> FastAPI:
    """建立並組裝 task-api;可注入自訂 repository(測試用)。"""
    repo = repository if repository is not None else InMemoryTaskRepository()
    app = FastAPI(title="task-api")
    app.state.task_service = TaskService(repo)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(TaskNotFoundError)
    async def handle_not_found(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    app.include_router(router)
    return app


app = create_app()
