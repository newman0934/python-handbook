"""Part 5 練習:泛型函式(承 05-generics-typevar,PEP 695)。"""

from __future__ import annotations


def first[T](items: list[T]) -> T | None:
    """回傳第一個元素,空 list 回 None。"""
    return items[0] if items else None


def last[T](items: list[T]) -> T | None:
    """回傳最後一個元素,空 list 回 None。"""
    return items[-1] if items else None
