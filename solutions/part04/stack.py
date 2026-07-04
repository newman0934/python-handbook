"""Part 4 練習:Stack 類別(承 01-class-and-instance / 08-dunder-methods)。"""

from __future__ import annotations


class Stack:
    """後進先出(LIFO)堆疊。"""

    def __init__(self) -> None:
        self._items: list[int] = []

    def push(self, x: int) -> None:
        self._items.append(x)

    def pop(self) -> int:
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> int:
        if not self._items:
            raise IndexError("peek from empty stack")
        return self._items[-1]

    def is_empty(self) -> bool:
        return not self._items

    def __len__(self) -> int:
        return len(self._items)
