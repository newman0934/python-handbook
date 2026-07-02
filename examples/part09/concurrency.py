"""Part 9 並發與並行的可執行範例。

對應章節：chapters/09-concurrency/
注意：範例聚焦「行為正確性」而非計時（計時依機器而異，不放進測試）。
"""

from __future__ import annotations

import asyncio
import queue
import threading
from concurrent.futures import ThreadPoolExecutor


def classify_task(task_type: str) -> str:
    """依任務類型推薦並發模型（Part 1/13 的決策）。"""
    if task_type == "cpu":
        return "multiprocessing"
    if task_type == "io_small":
        return "threading"
    if task_type == "io_large":
        return "asyncio"
    return "unknown"


# --- 競態條件：無鎖 vs 有鎖 ---
def counter_with_lock(threads_count: int, per_thread: int) -> int:
    """用 Lock 保護共享計數器，結果正確。"""
    counter = 0
    lock = threading.Lock()

    def increment() -> None:
        nonlocal counter
        for _ in range(per_thread):
            with lock:
                counter += 1

    threads = [threading.Thread(target=increment) for _ in range(threads_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return counter


# --- 生產者-消費者：用 Queue 傳遞而非共享 ---
def producer_consumer(items: list[int]) -> list[int]:
    q: queue.Queue[int | None] = queue.Queue()
    processed: list[int] = []

    def producer() -> None:
        for item in items:
            q.put(item)
        q.put(None)  # 哨兵

    def consumer() -> None:
        while True:
            item = q.get()
            if item is None:
                break
            processed.append(item * 2)

    p = threading.Thread(target=producer)
    c = threading.Thread(target=consumer)
    p.start()
    c.start()
    p.join()
    c.join()
    return processed


# --- ThreadPoolExecutor ---
def io_work(x: int) -> int:
    return x * x


def thread_pool_map(data: list[int]) -> list[int]:
    with ThreadPoolExecutor(max_workers=4) as executor:
        return list(executor.map(io_work, data))


# --- asyncio：gather 並發 ---
async def async_fetch(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"{name}"


async def gather_all(names: list[str]) -> list[str]:
    return await asyncio.gather(*(async_fetch(n, 0.01) for n in names))


# --- asyncio：Semaphore 限流 ---
async def limited_fetch(name: str, sem: asyncio.Semaphore) -> str:
    async with sem:
        return await async_fetch(name, 0.01)


async def gather_limited(names: list[str], limit: int) -> list[str]:
    sem = asyncio.Semaphore(limit)
    return await asyncio.gather(*(limited_fetch(n, sem) for n in names))


# --- asyncio：to_thread 跑阻塞工作 ---
def blocking_double(x: int) -> int:
    return x * 2  # 模擬阻塞工作（實際會 sleep，測試用純函式）


async def run_blocking(data: list[int]) -> list[int]:
    return await asyncio.gather(*(asyncio.to_thread(blocking_double, x) for x in data))
