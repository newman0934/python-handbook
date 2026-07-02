"""Part 7 迭代器與生成器的可執行範例。

對應章節：chapters/07-iterators-generators/
"""

from __future__ import annotations

import itertools as it
from collections.abc import Generator, Iterable, Iterator


# --- 可重複遍歷的可迭代物件（__iter__ 用生成器） ---
class Fibonacci:
    def __init__(self, n: int) -> None:
        self.n = n

    def __iter__(self) -> Iterator[int]:
        a, b = 0, 1
        for _ in range(self.n):
            yield a
            a, b = b, a + b


# --- 生成器函式 ---
def naturals() -> Iterator[int]:
    n = 0
    while True:
        yield n
        n += 1


def read_in_chunks(text: str, size: int) -> Iterator[str]:
    for i in range(0, len(text), size):
        yield text[i : i + size]


# --- yield from：遞迴扁平化 ---
def flatten(nested: Iterable[object]) -> Iterator[object]:
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item


def chain_all(*iterables: Iterable[int]) -> Iterator[int]:
    for iterable in iterables:
        yield from iterable


# --- 惰性管線 ---
def parse_rows(lines: Iterator[str]) -> Iterator[list[str]]:
    for line in lines:
        yield line.split(",")


def filter_valid(rows: Iterator[list[str]], width: int) -> Iterator[list[str]]:
    for row in rows:
        if len(row) == width:
            yield row


def pipeline(text: str) -> list[list[str]]:
    lines = iter(text.splitlines())
    return list(filter_valid(parse_rows(lines), 3))


# --- itertools ---
def take(gen: Iterator[int], k: int) -> list[int]:
    return list(it.islice(gen, k))


def group_by_first_letter(words: list[str]) -> dict[str, list[str]]:
    words_sorted = sorted(words, key=lambda w: w[0])
    return {k: list(g) for k, g in it.groupby(words_sorted, key=lambda w: w[0])}


# --- generator 協程 ---
def running_average() -> Generator[float, float, None]:
    total = 0.0
    count = 0
    average = 0.0
    while True:
        value = yield average
        total += value
        count += 1
        average = total / count
