"""Part 14 app 測試(TestClient)。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from exercises.part14.app import create_app


def test_health() -> None:
    client = TestClient(create_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_get_item() -> None:
    client = TestClient(create_app())
    created = client.post("/items", json={"name": "book", "price": 9.9})
    assert created.status_code == 200
    body = created.json()
    assert body["name"] == "book"
    item_id = body["id"]
    fetched = client.get(f"/items/{item_id}")
    assert fetched.status_code == 200
    assert fetched.json() == {"id": item_id, "name": "book", "price": 9.9}


def test_get_missing_returns_404() -> None:
    client = TestClient(create_app())
    assert client.get("/items/999").status_code == 404
