"""Part 9 練習:平行 map(承 06-concurrent-futures)。

實作 parallel_map:用 concurrent.futures.ThreadPoolExecutor 平行套用 func,
結果順序需與輸入相同(提示:executor.map 會保序)。
"""

from __future__ import annotations

from collections.abc import Callable


def parallel_map(func: Callable[[int], int], nums: list[int], workers: int = 4) -> list[int]:
    """用執行緒池平行套用 func,回傳與輸入『同順序』的結果。"""
    raise NotImplementedError("實作我!")
