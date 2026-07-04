"""Part 22 練習:一致性雜湊環(承 05-caching-strategies / 分片)。

實作 ConsistentHashRing:add_node(每節點放 replicas 個虛擬節點)、
get_node(回傳環上順時針第一個節點;空環回 None)。同一 key 映射需穩定。
提示:用 bisect 在排序的雜湊值上找位置。
"""

from __future__ import annotations

import hashlib


class ConsistentHashRing:
    def __init__(self, replicas: int = 3) -> None:
        raise NotImplementedError("實作我!")

    @staticmethod
    def _hash(key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node: str) -> None:
        raise NotImplementedError("實作我!")

    def get_node(self, key: str) -> str | None:
        raise NotImplementedError("實作我!")
