"""Part 14 ch21 測試：迷你任務佇列的重試與死信。"""

from __future__ import annotations

from examples.part14.task_queue import Task, Worker


def test_successful_task_is_processed() -> None:
    log: list[str] = []
    worker = Worker(handlers={"ok": lambda p: log.append("ran")})
    worker.enqueue(Task("ok", {}))
    worker.drain()
    assert worker.processed == ["ok"]
    assert log == ["ran"]
    assert worker.dead_letter == []


def test_transient_failure_is_retried_then_succeeds() -> None:
    state = {"n": 0}

    def flaky(payload: dict[str, object]) -> None:
        state["n"] += 1
        if state["n"] < 2:
            raise RuntimeError("暫時失敗")

    worker = Worker(handlers={"flaky": flaky})
    worker.enqueue(Task("flaky", {}))
    worker.drain()
    assert worker.processed == ["flaky"]  # 第二次成功
    assert state["n"] == 2
    assert worker.dead_letter == []


def test_permanent_failure_goes_to_dead_letter() -> None:
    def boom(payload: dict[str, object]) -> None:
        raise RuntimeError("永久失敗")

    worker = Worker(handlers={"bad": boom})
    worker.enqueue(Task("bad", {}, max_retries=2))
    worker.drain()
    assert worker.processed == []
    assert len(worker.dead_letter) == 1
    assert worker.dead_letter[0].attempts == 2  # 用盡重試才進死信
