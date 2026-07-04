"""Part 9 練習:asyncio.gather(承 07-asyncio-basics / 09-asyncio-tasks)。"""

from __future__ import annotations

import asyncio


async def double(x: int) -> int:
    """模擬非同步工作:讓出控制權後回傳 x*2。"""
    await asyncio.sleep(0)
    return x * 2


async def double_all(nums: list[int]) -> list[int]:
    """並行對每個數字做 double,保序回傳。"""
    results: list[int] = await asyncio.gather(*(double(n) for n in nums))
    return results
