"""Part 22 idempotency 測試。"""

from __future__ import annotations

from exercises.part22.idempotency import IdempotencyStore


def test_same_key_computes_once() -> None:
    store = IdempotencyStore()
    calls = {"n": 0}

    def compute() -> int:
        calls["n"] += 1
        return 42

    assert store.process("k1", compute) == 42
    assert store.process("k1", compute) == 42
    assert calls["n"] == 1  # 第二次不再計算


def test_different_keys_compute_separately() -> None:
    store = IdempotencyStore()
    assert store.process("a", lambda: 1) == 1
    assert store.process("b", lambda: 2) == 2
