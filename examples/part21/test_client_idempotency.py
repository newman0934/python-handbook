"""Part 21 ch10 測試：冪等鍵與 asyncio 取消。"""

from __future__ import annotations

import asyncio

from examples.part21.client_idempotency import (
    IdempotentSender,
    call_with_deadline,
    make_idempotency_key,
)


def test_key_is_stable_regardless_of_param_order() -> None:
    a = make_idempotency_key("charge", order_id="A1", amount=100)
    b = make_idempotency_key("charge", amount=100, order_id="A1")
    assert a == b


def test_different_params_give_different_key() -> None:
    a = make_idempotency_key("charge", order_id="A1", amount=100)
    b = make_idempotency_key("charge", order_id="A1", amount=200)
    assert a != b


def test_retry_with_same_key_calls_downstream_once() -> None:
    sender = IdempotentSender()
    key = make_idempotency_key("charge", order_id="A1")
    assert sender.send(key, lambda: "charged") == "charged"
    assert sender.send(key, lambda: "charged") == "charged"  # 重送
    assert sender.calls == 1  # 下游只被打一次


def test_deadline_cancels_slow_call() -> None:
    async def slow() -> str:
        await asyncio.sleep(10)
        return "done"

    result = asyncio.run(call_with_deadline(slow, 0.01))
    assert result == "timeout-cancelled"


def test_fast_call_completes_within_deadline() -> None:
    async def fast() -> str:
        return "ok"

    result = asyncio.run(call_with_deadline(fast, 1.0))
    assert result == "ok"
