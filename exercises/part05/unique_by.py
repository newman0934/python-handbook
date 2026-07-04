"""Part 5 練習:泛型 + 高階函式(承 05-generics-typevar / Part 8)。

實作 unique_by:依 key(x) 去重、保留首次出現順序。
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable


def unique_by[T](items: Iterable[T], key: Callable[[T], Hashable]) -> list[T]:
    """依 key(x) 去重,保留首次出現順序。"""
    raise NotImplementedError("實作我!")
