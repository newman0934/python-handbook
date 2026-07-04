"""Part 4 temperature 測試。"""

from __future__ import annotations

import pytest

from solutions.part04.temperature import Temperature


def test_celsius_to_fahrenheit() -> None:
    assert Temperature(100).fahrenheit == pytest.approx(212)
    assert Temperature(0).fahrenheit == pytest.approx(32)


def test_set_fahrenheit_updates_celsius() -> None:
    t = Temperature()
    t.fahrenheit = 212
    assert t.celsius == pytest.approx(100)


def test_below_absolute_zero_raises() -> None:
    with pytest.raises(ValueError):
        Temperature(-300)
