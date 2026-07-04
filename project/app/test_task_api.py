"""task-api 測試:HTTP 端到端(TestClient)+ service 單元(脫離 HTTP)。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from project.app.exceptions import TaskNotFoundError
from project.app.main import create_app
from project.app.models.task import TaskCreate
from project.app.repository.memory import InMemoryTaskRepository
from project.app.service.task_service import TaskService


def _client() -> TestClient:
    return TestClient(create_app())


def test_health() -> None:
    assert _client().get("/health").json() == {"status": "ok"}


def test_create_returns_201_and_get() -> None:
    client = _client()
    created = client.post("/tasks", json={"title": "buy milk"})
    assert created.status_code == 201
    task_id = created.json()["id"]
    fetched = client.get(f"/tasks/{task_id}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "buy milk"
    assert fetched.json()["done"] is False


def test_list_tasks() -> None:
    client = _client()
    client.post("/tasks", json={"title": "a"})
    client.post("/tasks", json={"title": "b"})
    assert len(client.get("/tasks").json()) == 2


def test_complete_task() -> None:
    client = _client()
    task_id = client.post("/tasks", json={"title": "x"}).json()["id"]
    completed = client.post(f"/tasks/{task_id}/complete")
    assert completed.json()["done"] is True


def test_update_task() -> None:
    client = _client()
    task_id = client.post("/tasks", json={"title": "x"}).json()["id"]
    updated = client.patch(f"/tasks/{task_id}", json={"title": "y"})
    assert updated.json()["title"] == "y"


def test_delete_task() -> None:
    client = _client()
    task_id = client.post("/tasks", json={"title": "x"}).json()["id"]
    assert client.delete(f"/tasks/{task_id}").status_code == 204
    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_get_missing_returns_404() -> None:
    assert _client().get("/tasks/999").status_code == 404


def test_create_empty_title_422() -> None:
    assert _client().post("/tasks", json={"title": ""}).status_code == 422


# --- service 層單元測試(不經 HTTP,示範分層可獨立測試) ---


def test_service_get_missing_raises() -> None:
    service = TaskService(InMemoryTaskRepository())
    with pytest.raises(TaskNotFoundError):
        service.get(1)


def test_service_create_and_complete() -> None:
    service = TaskService(InMemoryTaskRepository())
    task = service.create(TaskCreate(title="t"))
    assert task.done is False
    assert service.complete(task.id).done is True


def test_service_delete_missing_raises() -> None:
    service = TaskService(InMemoryTaskRepository())
    with pytest.raises(TaskNotFoundError):
        service.delete(42)
