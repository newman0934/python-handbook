"""Part 14 ch22：Celery 的兩個可轉移核心概念（純標準庫版）。

對應章節：chapters/14-web/22-celery.md

真正的 Celery 需要 broker（Redis/RabbitMQ），CI 不便啟動；但它最關鍵的兩個
「你一定要會」的概念是純邏輯、可獨立測試的：
- retry_backoff：重試的指數退避 + 抖動（full jitter），避免重試風暴。
- IdempotentProcessor：冪等去重，讓「至少一次投遞」下重複執行只生效一次。
章節裡的 Celery 程式碼是真實寫法（示意），這裡抽出可跑可測的核心。
"""

from __future__ import annotations

import random


def retry_backoff(
    attempt: int, base: float = 1.0, cap: float = 60.0, rng: random.Random | None = None
) -> float:
    """第 attempt 次重試該等幾秒：指數成長、封頂、加抖動（full jitter）。

    退避讓失敗的重試間隔越拉越長；抖動讓大量 client 不要「同時」重試打爆下游。
    """
    rng = rng or random.Random()
    ceiling = min(cap, base * (2**attempt))
    return rng.uniform(0, ceiling)


class IdempotentProcessor:
    """用冪等鍵去重：同一個 key 只真正生效一次。"""

    def __init__(self) -> None:
        self.seen: set[str] = set()
        self.effects: list[str] = []

    def process(self, key: str, effect: str) -> bool:
        """回傳 True=首次執行（產生效果），False=重複、已跳過。"""
        if key in self.seen:
            return False
        self.seen.add(key)
        self.effects.append(effect)
        return True


def demo() -> None:
    rng = random.Random(42)
    delays = [round(retry_backoff(a, rng=rng), 2) for a in range(6)]
    print("重試退避秒數（attempt 0..5）:", delays)

    processor = IdempotentProcessor()
    print("首次扣款:", processor.process("order-1", "charge"))
    print("重複投遞:", processor.process("order-1", "charge"))
    print("實際效果:", processor.effects)


if __name__ == "__main__":
    demo()
