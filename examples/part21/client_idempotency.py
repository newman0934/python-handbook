"""Part 21 ch10：呼叫別人時的冪等鍵與 asyncio 取消。

對應章節：chapters/21-microservices/10-client-idempotency-cancellation.md

- make_idempotency_key：由操作 + 參數算出穩定的冪等鍵，重試時用「同一把鍵」。
- IdempotentSender：帶冪等鍵送請求，重送只真正打下游一次（去重）。
- call_with_deadline：用 asyncio.wait_for 給呼叫設死線，逾時就取消。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable


def make_idempotency_key(operation: str, **params: object) -> str:
    """由操作名 + 參數算出穩定的鍵（同參數 → 同鍵，重試才共用一把鍵）。"""
    blob = operation + "|" + json.dumps(params, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


class IdempotentSender:
    """帶冪等鍵送請求：同一把鍵重送，只真正呼叫下游一次，之後回既有結果。"""

    def __init__(self) -> None:
        self._done: dict[str, str] = {}
        self.calls = 0

    def send(self, key: str, do_call: Callable[[], str]) -> str:
        if key in self._done:
            return self._done[key]  # 重送 → 回既有結果，不再打下游
        self.calls += 1
        result = do_call()
        self._done[key] = result
        return result


async def call_with_deadline(
    coro_fn: Callable[[], Awaitable[str]], deadline: float
) -> str:
    """給一次呼叫設死線；逾時就取消底層 coroutine，回傳 fallback。"""
    try:
        return await asyncio.wait_for(coro_fn(), timeout=deadline)
    except TimeoutError:
        return "timeout-cancelled"


def demo() -> None:
    key = make_idempotency_key("charge", order_id="A1", amount=100)
    same = make_idempotency_key("charge", amount=100, order_id="A1")
    print("冪等鍵:", key, "| 參數順序不同但同鍵:", key == same)

    sender = IdempotentSender()
    print("首次送出:", sender.send(key, lambda: "charged"))
    print("重送(逾時重試):", sender.send(key, lambda: "charged"))
    print("下游實際被呼叫次數:", sender.calls)

    async def slow() -> str:
        await asyncio.sleep(10)
        return "done"

    print("設 0.01s 死線:", asyncio.run(call_with_deadline(slow, 0.01)))


if __name__ == "__main__":
    demo()
