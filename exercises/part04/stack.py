"""Part 4 練習:Stack 類別(承 01-class-and-instance / 08-dunder-methods)。

實作 Stack 讓測試轉綠:push/pop/peek/is_empty/__len__。
空堆疊 pop/peek 要丟 IndexError。
"""

from __future__ import annotations


class Stack:
    """後進先出(LIFO)堆疊。"""

    def __init__(self) -> None:
        raise NotImplementedError("實作我!")

    def push(self, x: int) -> None:
        raise NotImplementedError("實作我!")

    def pop(self) -> int:
        raise NotImplementedError("實作我!")

    def peek(self) -> int:
        raise NotImplementedError("實作我!")

    def is_empty(self) -> bool:
        raise NotImplementedError("實作我!")

    def __len__(self) -> int:
        raise NotImplementedError("實作我!")
