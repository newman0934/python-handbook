"""Part 9 範例的驗證測試。

執行：pytest examples/part09
"""

import asyncio

import pytest

from examples.part09.concurrency import (
    classify_task,
    counter_with_lock,
    gather_all,
    gather_limited,
    producer_consumer,
    run_blocking,
    thread_pool_map,
)


@pytest.mark.parametrize(
    ("task_type", "expected"),
    [
        ("cpu", "multiprocessing"),
        ("io_small", "threading"),
        ("io_large", "asyncio"),
    ],
)
def test_classify_task(task_type: str, expected: str) -> None:
    assert classify_task(task_type) == expected


def test_lock_prevents_race() -> None:
    # 有鎖保護，結果一定正確（4 執行緒 × 50000）
    assert counter_with_lock(4, 50_000) == 200_000


def test_producer_consumer() -> None:
    assert producer_consumer([1, 2, 3, 4]) == [2, 4, 6, 8]


def test_thread_pool_map() -> None:
    assert thread_pool_map([1, 2, 3, 4]) == [1, 4, 9, 16]


def test_asyncio_gather() -> None:
    result = asyncio.run(gather_all(["a", "b", "c"]))
    assert result == ["a", "b", "c"]  # 依輸入順序


def test_asyncio_semaphore_limit() -> None:
    result = asyncio.run(gather_limited(["a", "b", "c", "d", "e"], limit=2))
    assert sorted(result) == ["a", "b", "c", "d", "e"]


def test_asyncio_to_thread() -> None:
    result = asyncio.run(run_blocking([1, 2, 3]))
    assert result == [2, 4, 6]
