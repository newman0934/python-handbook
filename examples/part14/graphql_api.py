"""Part 14（補充）GraphQL 迷你 resolver + API 設計實務（分頁/ETag/版本）。純標準庫。"""

from __future__ import annotations

import hashlib

# 一個查詢欄位：純量欄位名，或巢狀 (欄位名, 子欄位清單)
type Field = str | tuple[str, list[str]]

# ===== GraphQL：客戶端指定欄位 → 只回這些（含巢狀）=====
_DB: dict[str, dict[int, dict[str, object]]] = {
    "users": {1: {"id": 1, "name": "Alice", "email": "a@x.com", "post_ids": [10, 11]}},
    "posts": {
        10: {"id": 10, "title": "Hello", "body": "..."},
        11: {"id": 11, "title": "World", "body": "..."},
    },
}


def resolve_user(user_id: int, selection: list[Field]) -> dict[str, object]:
    """依 selection 只回指定欄位（純量或巢狀 (name, subfields)）。"""
    user = _DB["users"][user_id]
    result: dict[str, object] = {}
    for field in selection:
        if isinstance(field, str):
            result[field] = user[field]
        else:
            name, subfields = field  # field 已收斂為 tuple[str, list[str]]
            if name == "posts":
                post_ids = user["post_ids"]
                assert isinstance(post_ids, list)
                result["posts"] = [{f: _DB["posts"][pid][f] for f in subfields} for pid in post_ids]
    return result


# ===== API 設計：分頁 / ETag / 版本 =====
def paginate[T](items: list[T], page: int, size: int) -> dict[str, object]:
    total = len(items)
    total_pages = (total + size - 1) // size
    start = (page - 1) * size
    return {
        "items": items[start : start + size],
        "page": page,
        "size": size,
        "total": total,
        "total_pages": total_pages,
    }


def make_etag(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()[:8]


def conditional_get(content: str, if_none_match: str | None) -> tuple[int, str | None]:
    if if_none_match == make_etag(content):
        return 304, None  # Not Modified
    return 200, content


def route_version(path: str) -> str:
    if path.startswith("/v1/"):
        return "v1"
    if path.startswith("/v2/"):
        return "v2"
    return "404"
