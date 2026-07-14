"""Part 21 ch09 測試：可靠客戶端的重試與預算。"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from examples.part21.reliable_client import (
    PermanentError,
    TimeoutBudget,
    TransientError,
    retry_call,
)


def _fake_clock() -> tuple[list[float], Callable[[], float], Callable[[float], None]]:
    state = [0.0]

    def clock() -> float:
        return state[0]

    def sleep(seconds: float) -> None:
        state[0] += seconds

    return state, clock, sleep


def test_succeeds_after_transient_failures() -> None:
    state, clock, sleep = _fake_clock()
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise TransientError("503")
        return "ok"

    budget = TimeoutBudget(10.0, clock)
    result = retry_call(flaky, max_attempts=5, budget=budget,
                        backoff=lambda a: 2.0**a, sleep=sleep)
    assert result == "ok"
    assert calls["n"] == 3


def test_permanent_error_is_not_retried() -> None:
    state, clock, sleep = _fake_clock()
    calls = {"n": 0}

    def bad() -> str:
        calls["n"] += 1
        raise PermanentError("404")

    budget = TimeoutBudget(10.0, clock)
    with pytest.raises(PermanentError):
        retry_call(bad, max_attempts=5, budget=budget,
                   backoff=lambda a: 1.0, sleep=sleep)
    assert calls["n"] == 1  # 只試一次


def test_budget_exhaustion_raises_timeout() -> None:
    state, clock, sleep = _fake_clock()

    def always_transient() -> str:
        raise TransientError("一直逾時")

    budget = TimeoutBudget(3.0, clock)
    with pytest.raises(TimeoutError):
        # 退避把時間吃光後，下一輪 budget.expired() 觸發 TimeoutError
        retry_call(always_transient, max_attempts=10, budget=budget,
                   backoff=lambda a: 2.0**a, sleep=sleep)


def test_exhausting_attempts_raises_timeout() -> None:
    state, clock, sleep = _fake_clock()

    def always_transient() -> str:
        raise TransientError("暫時")

    budget = TimeoutBudget(1000.0, clock)  # 預算充足，卡在次數上限
    with pytest.raises(TimeoutError):
        retry_call(always_transient, max_attempts=3, budget=budget,
                   backoff=lambda a: 0.0, sleep=sleep)
