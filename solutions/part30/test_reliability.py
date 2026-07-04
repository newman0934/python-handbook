"""Part 30 reliability 測試。"""

from __future__ import annotations

from solutions.part30.reliability import backoff_delays


def test_exponential() -> None:
    assert backoff_delays(5, base=1.0, cap=60.0) == [1.0, 2.0, 4.0, 8.0, 16.0]


def test_capped() -> None:
    assert backoff_delays(8, base=1.0, cap=60.0) == [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 60.0, 60.0]


def test_zero_attempts() -> None:
    assert backoff_delays(0) == []
