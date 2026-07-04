"""Part 5 練習:泛型函式(承 05-generics-typevar,PEP 695)。

實作 first / last(泛型,空 list 回 None)。可用 def first[T](...) 語法。
"""

from __future__ import annotations


def first[T](items: list[T]) -> T | None:
    """回傳第一個元素,空 list 回 None。"""
    raise NotImplementedError("實作我!")


def last[T](items: list[T]) -> T | None:
    """回傳最後一個元素,空 list 回 None。"""
    raise NotImplementedError("實作我!")
