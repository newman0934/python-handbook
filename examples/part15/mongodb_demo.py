"""Part 15 ch25 MongoDB / 文件資料庫 可執行範例。

用純 Python 迷你文件庫模擬 MongoDB 核心語意(CI 可驗證、不需 MongoDB):

- find 查詢運算子($gt/$gte/$lt/$in)、陣列多鍵、等值、投影
- aggregate 分組計數($group + $sum:1)
- embed vs reference 的讀取成本(內嵌 1 次 vs 參照 N+1)

真實 PyMongo / mongosh 語法見章節示意。
"""

from __future__ import annotations

from typing import Any

Doc = dict[str, Any]


def matches(doc: Doc, query: Doc) -> bool:
    """模擬 MongoDB find 比對:支援 $gt/$gte/$lt/$in、陣列多鍵、等值。"""
    for field, cond in query.items():
        val = doc.get(field)
        if isinstance(cond, dict):  # 運算子條件,如 {"$gt": 26}
            for op, operand in cond.items():
                if op == "$gt" and not (val is not None and val > operand):
                    return False
                if op == "$gte" and not (val is not None and val >= operand):
                    return False
                if op == "$lt" and not (val is not None and val < operand):
                    return False
                if op == "$in" and val not in operand:
                    return False
        elif isinstance(val, list):  # 陣列多鍵:{tags: "vip"} 比對成員
            if cond not in val:
                return False
        elif val != cond:  # 等值
            return False
    return True


def find(collection: list[Doc], query: Doc) -> list[Doc]:
    return [d for d in collection if matches(d, query)]


def group_count(collection: list[Doc], by: str) -> dict[Any, int]:
    """模擬 aggregate 的 $group + $sum:1(依欄位分組計數)。"""
    out: dict[Any, int] = {}
    for d in collection:
        out[d[by]] = out.get(d[by], 0) + 1
    return out


def read_cost_embedded(order: Doc) -> int:
    """內嵌:品項就在訂單文件裡 → 1 次讀取拿到全部。"""
    _ = order["items"]
    return 1


def read_cost_referenced(order: Doc, items_col: list[Doc]) -> int:
    """參照:訂單只存 itemIds → 1 次讀訂單 + N 次讀各品項(像 N+1)。"""
    reads = 1
    for item_id in order["itemIds"]:
        _ = find(items_col, {"_id": item_id})
        reads += 1
    return reads


def main() -> None:  # pragma: no cover
    users = [
        {"_id": 1, "name": "Alice", "age": 30, "tags": ["vip", "gold"]},
        {"_id": 2, "name": "Bob", "age": 25, "tags": ["normal"]},
    ]
    print("age>26:", [u["name"] for u in find(users, {"age": {"$gt": 26}})])
    print("tags=vip:", [u["name"] for u in find(users, {"tags": "vip"})])


if __name__ == "__main__":
    main()
