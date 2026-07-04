"""Part 20 rate_limiter 測試。"""

from __future__ import annotations

from solutions.part20.rate_limiter import TokenBucket


def test_allows_burst_up_to_capacity() -> None:
    b = TokenBucket(capacity=2, refill_rate=1)
    assert b.allow(now=0) is True
    assert b.allow(now=0) is True
    assert b.allow(now=0) is False  # 用完,拒絕


def test_refills_over_time() -> None:
    b = TokenBucket(capacity=2, refill_rate=1)  # 每秒補 1
    b.allow(now=0)
    b.allow(now=0)
    assert b.allow(now=0) is False
    assert b.allow(now=1) is True  # 過 1 秒補 1 個,放行


def test_refill_capped_at_capacity() -> None:
    b = TokenBucket(capacity=2, refill_rate=1)
    # 閒置很久也不會超過容量:仍只允許 2 次連續
    assert b.allow(now=100) is True
    assert b.allow(now=100) is True
    assert b.allow(now=100) is False
