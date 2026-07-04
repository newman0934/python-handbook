"""Part 3 練習:序列操作(承 01-list / 05-set-frozenset)。

實作 dedup(保序去重)與 chunk(分塊)讓測試轉綠。
"""

from __future__ import annotations


def dedup[T](items: list[T]) -> list[T]:
    """去除重複但保留首次出現順序。"""
    raise NotImplementedError("實作我!")


def chunk[T](items: list[T], size: int) -> list[list[T]]:
    """把 list 切成每塊 size 個(最後一塊可較短)。size<=0 時丟 ValueError。"""
    raise NotImplementedError("實作我!")
