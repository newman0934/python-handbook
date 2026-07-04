"""Part 24 stats 測試。"""

from __future__ import annotations

import pytest

from solutions.part24.stats import describe, growth_rate


def test_describe() -> None:
    d = describe([2.0, 4.0, 6.0])
    assert d["mean"] == 4.0
    assert d["median"] == 4.0


def test_growth_rate() -> None:
    assert growth_rate(100.0, 120.0) == pytest.approx(0.2)


def test_growth_rate_zero_old() -> None:
    with pytest.raises(ValueError):
        growth_rate(0.0, 10.0)
