"""Part 9 練習:平行 map(承 06-concurrent-futures)。"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor


def parallel_map(func: Callable[[int], int], nums: list[int], workers: int = 4) -> list[int]:
    """用執行緒池平行套用 func,回傳與輸入『同順序』的結果。"""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(func, nums))
