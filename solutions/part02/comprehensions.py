"""Part 2 練習:comprehension(承 13-comprehensions)。"""

from __future__ import annotations


def flatten(matrix: list[list[int]]) -> list[int]:
    """把二維 list 攤平成一維(用 comprehension)。"""
    return [x for row in matrix for x in row]


def evens_squared(n: int) -> list[int]:
    """回傳 0..n-1 之中偶數的平方(用 comprehension)。"""
    return [x * x for x in range(n) if x % 2 == 0]


def char_positions(text: str) -> dict[str, list[int]]:
    """回傳每個字元出現的所有索引位置。"""
    out: dict[str, list[int]] = {}
    for i, ch in enumerate(text):
        out.setdefault(ch, []).append(i)
    return out
