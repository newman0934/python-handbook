"""Part 21 ch09：作為可靠 HTTP 客戶端的核心邏輯（逾時預算 + 重試退避）。

對應章節：chapters/21-microservices/09-reliable-http-client.md

呼叫第三方 / 下游服務時的可靠性三件事，抽成純邏輯（時鐘與 sleep 注入，可測）：
- TimeoutBudget：整趟呼叫共享一個總時間預算（deadline propagation），跨重試遞減。
- 只重試「暫時性」錯誤，永久性錯誤立刻放棄。
- 指數退避（配抖動於真實環境），且退避不超過剩餘預算。
真實環境用 httpx，把 fn 換成一次 HTTP 請求即可。
"""

from __future__ import annotations

from collections.abc import Callable


class TransientError(Exception):
    """暫時性失敗（逾時、503、連線重置）——值得重試。"""


class PermanentError(Exception):
    """永久性失敗（400、401、404）——重試也沒用，立刻放棄。"""


class TimeoutBudget:
    """整趟呼叫的總時間預算，跨重試共享（deadline propagation）。"""

    def __init__(self, total: float, clock: Callable[[], float]) -> None:
        self._deadline = clock() + total
        self._clock = clock

    def remaining(self) -> float:
        return self._deadline - self._clock()

    def expired(self) -> bool:
        return self.remaining() <= 0


def retry_call(
    fn: Callable[[], str],
    *,
    max_attempts: int,
    budget: TimeoutBudget,
    backoff: Callable[[int], float],
    sleep: Callable[[float], None],
) -> str:
    """重試 fn：只重試 TransientError，尊重預算，退避不超過剩餘時間。"""
    last: Exception | None = None
    for attempt in range(max_attempts):
        if budget.expired():
            raise TimeoutError("逾時預算用盡")
        try:
            return fn()
        except PermanentError:
            raise  # 永久錯誤不重試
        except TransientError as e:
            last = e
            if attempt + 1 < max_attempts:
                sleep(min(backoff(attempt), max(budget.remaining(), 0)))
    raise TimeoutError("重試用盡") from last


def demo() -> None:
    now = {"t": 0.0}

    def clock() -> float:
        return now["t"]

    def sleep(seconds: float) -> None:
        now["t"] += seconds

    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise TransientError("下游暫時 503")
        return "ok"

    budget = TimeoutBudget(total=10.0, clock=clock)
    result = retry_call(
        flaky, max_attempts=5, budget=budget, backoff=lambda a: 2.0**a, sleep=sleep
    )
    print("結果:", result)
    print("嘗試次數:", calls["n"], "耗用時間:", now["t"])


if __name__ == "__main__":
    demo()
