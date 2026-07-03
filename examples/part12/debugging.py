"""Part 12（補充）除錯範例：可測試的 bug 對照與 traceback 擷取。純標準庫。"""

from __future__ import annotations

import traceback


def buggy_average(nums: list[float]) -> float:
    """有 bug：分母用了 len+1（off-by-one）。"""
    return sum(nums) / (len(nums) + 1)


def correct_average(nums: list[float]) -> float:
    if not nums:
        raise ValueError("空序列無法算平均")
    return sum(nums) / len(nums)


def last_traceback_line(exc: BaseException) -> str:
    """取例外 traceback 的最後一行（讀 traceback 先看這裡）。"""
    lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    return "".join(lines).strip().splitlines()[-1]
