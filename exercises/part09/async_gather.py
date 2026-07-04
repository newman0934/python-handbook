"""Part 9 練習:asyncio.gather(承 07-asyncio-basics / 09-asyncio-tasks)。

實作 double(await asyncio.sleep(0) 後回 x*2)與 double_all
(用 asyncio.gather 並行處理、保序回傳)。
"""

from __future__ import annotations


async def double(x: int) -> int:
    """模擬非同步工作:讓出控制權後回傳 x*2。"""
    raise NotImplementedError("實作我!")


async def double_all(nums: list[int]) -> list[int]:
    """並行對每個數字做 double,保序回傳。"""
    raise NotImplementedError("實作我!")
