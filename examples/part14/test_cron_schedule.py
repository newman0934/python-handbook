"""Part 14 ch23 測試：cron 運算式比對。"""

from __future__ import annotations

from datetime import datetime

from examples.part14.cron_schedule import cron_matches


def test_daily_at_3am() -> None:
    assert cron_matches("0", "3", "*", "*", "*", datetime(2026, 7, 14, 3, 0)) is True
    assert cron_matches("0", "3", "*", "*", "*", datetime(2026, 7, 14, 3, 1)) is False
    assert cron_matches("0", "3", "*", "*", "*", datetime(2026, 7, 14, 4, 0)) is False


def test_step_every_15_minutes() -> None:
    for minute in (0, 15, 30, 45):
        assert cron_matches("*/15", "*", "*", "*", "*", datetime(2026, 7, 14, 9, minute))
    assert cron_matches("*/15", "*", "*", "*", "*", datetime(2026, 7, 14, 9, 31)) is False


def test_range_business_hours() -> None:
    # 週一到週五（1-5）的 9-17 點整點
    spec = ("0", "9-17", "*", "*", "1-5")
    assert cron_matches(*spec, dt=datetime(2026, 7, 14, 9, 0)) is True   # 週二 09:00
    assert cron_matches(*spec, dt=datetime(2026, 7, 14, 18, 0)) is False  # 超過 17
    assert cron_matches(*spec, dt=datetime(2026, 7, 12, 10, 0)) is False  # 週日


def test_list_of_values() -> None:
    # 每小時的第 0、30 分
    assert cron_matches("0,30", "*", "*", "*", "*", datetime(2026, 7, 14, 9, 30)) is True
    assert cron_matches("0,30", "*", "*", "*", "*", datetime(2026, 7, 14, 9, 15)) is False
