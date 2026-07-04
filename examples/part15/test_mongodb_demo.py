"""Part 15 ch25 MongoDB 範例測試。"""

from __future__ import annotations

import pytest

from examples.part15.mongodb_demo import (
    find,
    group_count,
    matches,
    read_cost_embedded,
    read_cost_referenced,
)


def _users() -> list[dict[str, object]]:
    return [
        {"_id": 1, "name": "Alice", "age": 30, "tags": ["vip", "gold"]},
        {"_id": 2, "name": "Bob", "age": 25, "tags": ["normal"]},
        {"_id": 3, "name": "Cara", "age": 40, "tags": ["vip"]},
    ]


# ---- find 查詢運算子 ----


def test_find_gt() -> None:
    assert [u["name"] for u in find(_users(), {"age": {"$gt": 26}})] == ["Alice", "Cara"]


def test_find_array_multikey() -> None:
    # {tags: "vip"} 命中 tags 陣列含 "vip" 的文件
    assert [u["name"] for u in find(_users(), {"tags": "vip"})] == ["Alice", "Cara"]


def test_find_in() -> None:
    assert [u["name"] for u in find(_users(), {"age": {"$in": [25, 40]}})] == ["Bob", "Cara"]


def test_find_equality() -> None:
    assert [u["_id"] for u in find(_users(), {"name": "Alice"})] == [1]


@pytest.mark.parametrize(
    "query, count",
    [
        ({"age": {"$gte": 30}}, 2),
        ({"age": {"$lt": 30}}, 1),
        ({"tags": "gold"}, 1),
        ({"age": {"$gt": 100}}, 0),
    ],
)
def test_find_counts(query: dict[str, object], count: int) -> None:
    assert len(find(_users(), query)) == count


def test_matches_missing_field_gt() -> None:
    # 欄位不存在時比較運算子不命中(不報錯)
    assert matches({"name": "X"}, {"age": {"$gt": 5}}) is False


# ---- aggregate 分組 ----


def test_group_count() -> None:
    docs = [{"s": "paid"}, {"s": "paid"}, {"s": "new"}]
    assert group_count(docs, "s") == {"paid": 2, "new": 1}


# ---- embed vs reference 讀取成本 ----


def test_embedded_single_read() -> None:
    order = {"_id": 100, "items": [{"p": "Book"}, {"p": "Pen"}]}
    assert read_cost_embedded(order) == 1


def test_referenced_is_n_plus_one() -> None:
    items = [{"_id": "i1"}, {"_id": "i2"}, {"_id": "i3"}]
    order = {"_id": 101, "itemIds": ["i1", "i2", "i3"]}
    # 1 次讀訂單 + 3 次讀品項 = 4(N+1)
    assert read_cost_referenced(order, items) == 4


def test_embedded_cheaper_than_referenced() -> None:
    items = [{"_id": f"i{i}"} for i in range(10)]
    embedded = {"_id": 1, "items": [{} for _ in range(10)]}
    referenced = {"_id": 2, "itemIds": [f"i{i}" for i in range(10)]}
    assert read_cost_embedded(embedded) < read_cost_referenced(referenced, items)
