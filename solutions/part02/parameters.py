"""Part 2 練習:*args / **kwargs(承 09-parameters-args-kwargs)。"""

from __future__ import annotations

from typing import Any


def running_total(*nums: int) -> list[int]:
    """回傳累加序列:running_total(1,2,3) -> [1,3,6]。無參數回 []。"""
    out: list[int] = []
    total = 0
    for n in nums:
        total += n
        out.append(total)
    return out


def merge_config(base: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    """回傳 base 疊加 overrides 的新 dict(不改動 base)。"""
    merged = dict(base)
    merged.update(overrides)
    return merged
