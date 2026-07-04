"""Part 15 ch24 MySQL 專屬功能 可執行範例。

用純 Python 模擬 MySQL/InnoDB 特有的引擎行為,CI 可驗證、不需 MySQL:

- InnoDB 聚簇索引:次要索引查詢的「兩次查找(回表)」vs 覆蓋索引
- utf8mb4 陷阱:哪些字元舊 utf8(utf8mb3, 3-byte)存不下
- AUTO_INCREMENT:rollback 後跳號(不回收)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InnoDBTable:
    """聚簇索引表:主鍵→完整列;次要索引:欄值→主鍵值(非列指標)。"""

    clustered: dict[int, dict[str, Any]] = field(default_factory=dict)
    secondary: dict[str, int] = field(default_factory=dict)
    traversals: int = 0

    def insert(self, pk: int, row: dict[str, Any]) -> None:
        self.clustered[pk] = row
        self.secondary[row["email"]] = pk  # 次要索引存的是主鍵值

    def find_by_email(self, email: str, covering: bool) -> dict[str, Any] | None:
        """covering=True 時只需次要索引(免回表);否則要兩次查找。"""
        self.traversals = 1  # 第 1 跳:查次要索引
        pk = self.secondary.get(email)
        if pk is None:
            return None
        if covering:
            return {"email": email, "pk": pk}  # 覆蓋索引:免回表
        self.traversals = 2  # 第 2 跳:回聚簇索引拿完整列
        return self.clustered[pk]


def fits_in_utf8mb3(text: str) -> bool:
    """MySQL 舊 utf8(utf8mb3)每字元上限 3 bytes;4-byte 字元存不下。"""
    return all(len(ch.encode("utf-8")) <= 3 for ch in text)


@dataclass
class AutoIncrement:
    counter: int = 0

    def next_id(self) -> int:
        self.counter += 1
        return self.counter  # rollback 也不退回 → 產生間隙


def main() -> None:  # pragma: no cover
    t = InnoDBTable()
    t.insert(1, {"email": "a@x.com", "name": "Alice"})
    t.find_by_email("a@x.com", covering=False)
    print("回表走訪次數:", t.traversals)
    print("emoji 需 utf8mb4:", not fits_in_utf8mb3("😀"))


if __name__ == "__main__":
    main()
