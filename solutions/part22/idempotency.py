"""Part 22 練習:冪等處理(承 06-idempotency)。"""

from __future__ import annotations

from collections.abc import Callable


class IdempotencyStore:
    """以 key 去重:同一 key 只計算一次,之後回快取結果。"""

    def __init__(self) -> None:
        self._results: dict[str, int] = {}

    def process(self, key: str, compute: Callable[[], int]) -> int:
        if key in self._results:
            return self._results[key]
        result = compute()
        self._results[key] = result
        return result
