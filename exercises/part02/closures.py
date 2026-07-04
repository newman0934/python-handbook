"""Part 2 練習:閉包(承 12-closures)。

實作 make_counter 與 make_accumulator 讓測試轉綠。
提示:用 nonlocal 讓內層函式修改外層變數。
"""

from __future__ import annotations

from collections.abc import Callable


def make_counter(start: int = 0) -> Callable[[], int]:
    """回傳一個計數器函式:每次呼叫回傳遞增後的值(從 start+1 開始)。"""
    raise NotImplementedError("實作我!")


def make_accumulator() -> Callable[[int], int]:
    """回傳一個累加器:每次呼叫把參數加進總和並回傳當前總和。"""
    raise NotImplementedError("實作我!")
