"""Part 18 效能優化範例：profiling / 資料結構 / 快取 / slots / 非同步。

以純函式封裝可驗證的「確定性行為」（呼叫次數、快取統計、結果正確性），
避免以絕對時間做斷言（時間依機器而異）。全部純 stdlib。
"""

from __future__ import annotations

import asyncio
import cProfile
import pstats
from collections import deque
from functools import cache, lru_cache


# ===== profiling：抽出各函式的呼叫次數（見 01）=====
def _slow_sum(n: int) -> int:
    total = 0
    for i in range(n):
        total += i
    return total


def _workload() -> int:
    s = 0
    for _ in range(3):
        s += _slow_sum(1_000)
    return s


def profile_call_counts() -> dict[str, int]:
    """用 cProfile 跑 workload，回傳各函式的呼叫次數（ncalls 是確定性的）。"""
    pr = cProfile.Profile()
    pr.enable()
    _workload()
    pr.disable()
    stats = pstats.Stats(pr)
    raw = stats.stats  # type: ignore[attr-defined]  # typeshed 未涵蓋此私有屬性
    return {func[2]: nc for func, (cc, nc, tt, ct, callers) in raw.items()}


# ===== 資料結構：O(n^2) vs O(n) 去重保序（見 03）=====
def dedup_slow(items: list[int]) -> list[int]:
    """in list 是 O(n) → 整體 O(n^2)。"""
    result: list[int] = []
    for x in items:
        if x not in result:
            result.append(x)
    return result


def dedup_fast(items: list[int]) -> list[int]:
    """in set 是 O(1) → 整體 O(n)；結果與 dedup_slow 相同。"""
    seen: set[int] = set()
    result: list[int] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def drain_deque(n: int) -> int:
    """deque.popleft 為 O(1)；回傳彈出的元素數。"""
    q = deque(range(n))
    count = 0
    while q:
        q.popleft()
        count += 1
    return count


# ===== 快取：記憶化 fib（見 04）=====
@cache
def memoized_fib(n: int) -> int:
    """記憶化 fib：相同輸入只算一次，O(2^n) → O(n)。"""
    if n < 2:
        return n
    return memoized_fib(n - 1) + memoized_fib(n - 2)


def fib_cache_stats(n: int) -> tuple[int, int, int]:
    """用獨立快取算 fib(n)，回傳 (hits, misses, currsize)。"""

    @cache
    def fib(k: int) -> int:
        if k < 2:
            return k
        return fib(k - 1) + fib(k - 2)

    fib(n)
    info = fib.cache_info()
    return info.hits, info.misses, info.currsize


def count_fib_calls_without_cache(n: int) -> int:
    """無快取的 fib 實際遞迴呼叫次數（示範重複計算的爆炸）。"""
    counter = {"n": 0}

    def fib(k: int) -> int:
        counter["n"] += 1
        if k < 2:
            return k
        return fib(k - 1) + fib(k - 2)

    fib(n)
    return counter["n"]


def lru_eviction_stats(maxsize: int, calls: list[int]) -> tuple[int, int, int | None, int]:
    """依序呼叫有限容量快取，回傳 (hits, misses, maxsize, currsize) 觀察 LRU 淘汰。"""

    @lru_cache(maxsize=maxsize)
    def square(x: int) -> int:
        return x * x

    for c in calls:
        square(c)
    info = square.cache_info()
    return info.hits, info.misses, info.maxsize, info.currsize


# ===== 記憶體：__slots__ vs __dict__（見 06）=====
class PointDict:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class PointSlots:
    __slots__ = ("x", "y")

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


def has_instance_dict(obj: object) -> bool:
    """實例是否帶 __dict__（__slots__ 類別為 False）。"""
    return hasattr(obj, "__dict__")


# ===== 非同步：併發重疊 I/O 等待（見 07）=====
async def _fetch(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"{name} done"


async def gather_fetch(names: list[str], delay: float) -> list[str]:
    """併發跑多個模擬 I/O，回傳結果（順序對應輸入）。"""
    return await asyncio.gather(*(_fetch(name, delay) for name in names))
