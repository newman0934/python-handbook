"""Part 22 練習:一致性雜湊環(承 05-caching-strategies / 分片)。"""

from __future__ import annotations

import bisect
import hashlib


class ConsistentHashRing:
    """一致性雜湊:每個節點放 replicas 個虛擬節點,key 映射到環上順時針第一個節點。"""

    def __init__(self, replicas: int = 3) -> None:
        self.replicas = replicas
        self._ring: dict[int, str] = {}
        self._sorted: list[int] = []

    @staticmethod
    def _hash(key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node: str) -> None:
        for i in range(self.replicas):
            h = self._hash(f"{node}:{i}")
            self._ring[h] = node
            bisect.insort(self._sorted, h)

    def get_node(self, key: str) -> str | None:
        if not self._sorted:
            return None
        h = self._hash(key)
        idx = bisect.bisect(self._sorted, h) % len(self._sorted)
        return self._ring[self._sorted[idx]]
