"""Part 20 練習:token bucket 限流(承 11-system-design-rate-limiter)。

實作 TokenBucket:allow(now) 依經過時間補充權杖(上限 capacity),
權杖足夠則扣除並回 True,否則 False。以注入的 now(秒)驅動,方便測試。
"""

from __future__ import annotations


class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        raise NotImplementedError("實作我!")

    def allow(self, now: float, cost: int = 1) -> bool:
        raise NotImplementedError("實作我!")
