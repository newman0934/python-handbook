"""Part 2 練習:*args / **kwargs(承 09-parameters-args-kwargs)。

實作 running_total 與 merge_config 讓測試轉綠。
"""

from __future__ import annotations

from typing import Any


def running_total(*nums: int) -> list[int]:
    """回傳累加序列:running_total(1,2,3) -> [1,3,6]。無參數回 []。"""
    raise NotImplementedError("實作我!")


def merge_config(base: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    """回傳 base 疊加 overrides 的新 dict(不改動 base)。"""
    raise NotImplementedError("實作我!")
