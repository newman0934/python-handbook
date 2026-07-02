"""Part 18 範例的驗證測試。

執行：pytest examples/part18
"""

from __future__ import annotations

import asyncio

import pytest

from examples.part18.performance import (
    PointDict,
    PointSlots,
    count_fib_calls_without_cache,
    dedup_fast,
    dedup_slow,
    drain_deque,
    fib_cache_stats,
    gather_fetch,
    has_instance_dict,
    lru_eviction_stats,
    memoized_fib,
    profile_call_counts,
)


# --- profiling：呼叫次數是確定性的（見 01）---
def test_profile_call_counts() -> None:
    counts = profile_call_counts()
    assert counts["_workload"] == 1
    assert counts["_slow_sum"] == 3  # 迴圈 3 圈各呼叫一次


# --- 資料結構：兩種去重結果一致且保序（見 03）---
def test_dedup_equivalence_and_order() -> None:
    data = [3, 1, 2, 3, 1, 4, 2, 5]
    assert dedup_slow(data) == dedup_fast(data)
    assert dedup_fast(data) == [3, 1, 2, 4, 5]  # 保序去重


def test_drain_deque() -> None:
    assert drain_deque(1000) == 1000


# --- 快取：記憶化正確性與 cache_info（見 04）---
def test_memoized_fib_correct() -> None:
    assert [memoized_fib(i) for i in range(10)] == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    assert memoized_fib(30) == 832040


def test_fib_cache_stats_deterministic() -> None:
    hits, misses, currsize = fib_cache_stats(30)
    assert misses == 31  # 31 個不同的 n 各算一次
    assert currsize == 31
    assert hits == 28


def test_fib_without_cache_explodes() -> None:
    # 無快取遞迴 fib(30) 呼叫次數爆炸
    assert count_fib_calls_without_cache(30) == 2_692_537


def test_lru_eviction() -> None:
    # 呼叫序列 1,2,3,2,1（maxsize=2）：算1 算2 算3(淘汰1) 2命中 1重算
    hits, misses, maxsize, currsize = lru_eviction_stats(2, [1, 2, 3, 2, 1])
    assert maxsize == 2
    assert currsize == 2
    assert hits == 1
    assert misses == 4


# --- 記憶體：__slots__ 行為（見 06）---
def test_slots_has_no_dict() -> None:
    assert has_instance_dict(PointDict(1, 2)) is True
    assert has_instance_dict(PointSlots(1, 2)) is False


def test_slots_rejects_undeclared_attribute() -> None:
    p = PointSlots(1, 2)
    with pytest.raises(AttributeError):
        p.z = 3  # type: ignore[attr-defined]


# --- 非同步：併發回傳正確結果（見 07）---
def test_gather_fetch_results() -> None:
    names = ["task0", "task1", "task2"]
    results = asyncio.run(gather_fetch(names, 0.01))
    assert results == ["task0 done", "task1 done", "task2 done"]
