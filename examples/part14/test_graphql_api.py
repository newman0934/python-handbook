"""Part 14（補充）GraphQL + API 設計範例的驗證測試。"""

from __future__ import annotations

from examples.part14.graphql_api import (
    conditional_get,
    make_etag,
    paginate,
    resolve_user,
    route_version,
)


# --- GraphQL：只回指定欄位 ---
def test_graphql_no_overfetch() -> None:
    assert resolve_user(1, ["name"]) == {"name": "Alice"}
    assert resolve_user(1, ["name", "email"]) == {"name": "Alice", "email": "a@x.com"}


def test_graphql_nested() -> None:
    result = resolve_user(1, ["name", ("posts", ["title"])])
    assert result == {"name": "Alice", "posts": [{"title": "Hello"}, {"title": "World"}]}


# --- API 設計：分頁 ---
def test_paginate() -> None:
    data = list(range(1, 101))
    p = paginate(data, page=2, size=10)
    assert p["items"] == list(range(11, 21))
    assert p["total_pages"] == 10
    assert p["total"] == 100


# --- API 設計：ETag 條件請求 ---
def test_conditional_get() -> None:
    content = "resource-v1"
    etag = make_etag(content)
    assert conditional_get(content, None) == (200, content)  # 首次
    assert conditional_get(content, etag) == (304, None)  # 沒變 → 304


# --- API 設計：版本路由 ---
def test_route_version() -> None:
    assert route_version("/v1/users") == "v1"
    assert route_version("/v2/users") == "v2"
    assert route_version("/other") == "404"
