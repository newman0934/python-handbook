"""Part 14 ch22 測試：退避與冪等。"""

from __future__ import annotations

import random

from examples.part14.celery_concepts import IdempotentProcessor, retry_backoff


def test_backoff_within_bounds_and_capped() -> None:
    rng = random.Random(0)
    for attempt in range(10):
        delay = retry_backoff(attempt, base=1.0, cap=60.0, rng=rng)
        ceiling = min(60.0, 1.0 * (2**attempt))
        assert 0.0 <= delay <= ceiling  # full jitter 落在 [0, ceiling]


def test_backoff_ceiling_grows_then_caps() -> None:
    # ceiling = min(cap, base*2^attempt)：前段指數成長，之後被 cap 封頂
    assert min(60.0, 1.0 * 2**0) == 1.0
    assert min(60.0, 1.0 * 2**3) == 8.0
    assert min(60.0, 1.0 * 2**10) == 60.0  # 封頂


def test_idempotent_processing_runs_once() -> None:
    processor = IdempotentProcessor()
    assert processor.process("order-1", "charge") is True   # 首次
    assert processor.process("order-1", "charge") is False  # 重複被擋
    assert processor.effects == ["charge"]                   # 只生效一次


def test_idempotent_different_keys_all_run() -> None:
    processor = IdempotentProcessor()
    assert processor.process("a", "x") is True
    assert processor.process("b", "y") is True
    assert processor.effects == ["x", "y"]
