"""Part 20 練習:token bucket 限流(承 11-system-design-rate-limiter)。"""

from __future__ import annotations


class TokenBucket:
    """權杖桶:容量 capacity,以 refill_rate(個/秒)補充。

    allow(now) 依外部注入的時間補充權杖,足夠則扣一個並允許。
    """

    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self._last = 0.0

    def allow(self, now: float, cost: int = 1) -> bool:
        elapsed = now - self._last
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self._last = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False
