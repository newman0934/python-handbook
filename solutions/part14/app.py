"""Part 14 練習解答:FastAPI 迷你 API(承 05-fastapi / 06-pydantic)。"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    price: float


class ItemOut(Item):
    id: int


def create_app() -> FastAPI:
    """建立 task/item API:健康檢查、建立、查詢(找不到回 404)。"""
    app = FastAPI()
    items: dict[int, Item] = {}
    state = {"next_id": 0}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/items")
    def create_item(item: Item) -> ItemOut:
        state["next_id"] += 1
        item_id = state["next_id"]
        items[item_id] = item
        return ItemOut(id=item_id, name=item.name, price=item.price)

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> ItemOut:
        stored = items.get(item_id)
        if stored is None:
            raise HTTPException(status_code=404, detail="item not found")
        return ItemOut(id=item_id, name=stored.name, price=stored.price)

    return app
