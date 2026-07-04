"""Part 8 decorators 測試。"""

from __future__ import annotations

from solutions.part08.decorators import double_result, memoize


def test_double_result() -> None:
    @double_result
    def add_one(x: int) -> int:
        return x + 1

    assert add_one(4) == 10  # (4+1)*2


def test_memoize_caches() -> None:
    calls = {"n": 0}

    @memoize
    def square(x: int) -> int:
        calls["n"] += 1
        return x * x

    assert square(3) == 9
    assert square(3) == 9
    assert calls["n"] == 1  # 第二次命中快取,不再計算


def test_wraps_preserves_name() -> None:
    @double_result
    def foo(x: int) -> int:
        return x

    assert foo.__name__ == "foo"
