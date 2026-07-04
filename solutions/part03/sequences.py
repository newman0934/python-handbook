"""Part 3 練習:序列操作(承 01-list / 05-set-frozenset)。"""

from __future__ import annotations


def dedup[T](items: list[T]) -> list[T]:
    """去除重複但保留首次出現順序。"""
    seen: set[T] = set()
    out: list[T] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def chunk[T](items: list[T], size: int) -> list[list[T]]:
    """把 list 切成每塊 size 個(最後一塊可較短)。size<=0 時丟 ValueError。"""
    if size <= 0:
        raise ValueError("size 必須 > 0")
    return [items[i : i + size] for i in range(0, len(items), size)]
