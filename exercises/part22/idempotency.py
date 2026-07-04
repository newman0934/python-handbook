"""Part 22 練習:冪等處理(承 06-idempotency)。

實作 IdempotencyStore.process(key, compute):相同 key 只執行一次 compute(),
之後直接回傳先前結果(避免重複扣款/重複送出)。
"""

from __future__ import annotations

from collections.abc import Callable


class IdempotencyStore:
    def __init__(self) -> None:
        raise NotImplementedError("實作我!")

    def process(self, key: str, compute: Callable[[], int]) -> int:
        raise NotImplementedError("實作我!")
