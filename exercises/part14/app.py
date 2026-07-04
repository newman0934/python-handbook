"""Part 14 練習:FastAPI 迷你 API(承 05-fastapi / 06-pydantic)。

實作 create_app(),提供三個端點讓 test_app.py 轉綠:
- GET  /health           -> {"status": "ok"}
- POST /items            body {"name": str, "price": float} -> {id, name, price}
- GET  /items/{item_id}  -> 該 item;不存在回 404

提示:用 pydantic BaseModel 定義 Item;用 app.get/app.post 註冊路由;
找不到用 HTTPException(status_code=404)。
"""

from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    """建立並回傳設定好路由的 FastAPI app。"""
    raise NotImplementedError("實作我!")
