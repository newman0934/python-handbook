"""Part 9 async_gather 測試。"""

from __future__ import annotations

import asyncio

from exercises.part09.async_gather import double, double_all


def test_double() -> None:
    assert asyncio.run(double(5)) == 10


def test_double_all() -> None:
    assert asyncio.run(double_all([1, 2, 3])) == [2, 4, 6]


def test_double_all_empty() -> None:
    assert asyncio.run(double_all([])) == []
