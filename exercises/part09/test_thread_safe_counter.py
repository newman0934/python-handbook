"""Part 9 thread_safe_counter 測試。"""

from __future__ import annotations

from exercises.part09.thread_safe_counter import SafeCounter, run_incrementers


def test_single_thread() -> None:
    c = SafeCounter()
    for _ in range(100):
        c.increment()
    assert c.value == 100


def test_concurrent_no_lost_updates() -> None:
    c = SafeCounter()
    total = run_incrementers(c, threads=8, per_thread=10_000)
    assert total == 80_000  # 有鎖保護 → 不丟失更新
