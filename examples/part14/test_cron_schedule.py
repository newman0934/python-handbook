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


def test_dom_and_dow_both_restricted_is_or() -> None:
    # 標準 cron：'0 0 13 * 5' = 每月 13 號 OR 每週五 的 00:00
    spec = ("0", "0", "13", "*", "5")
    # 2026-07-13 是週一但正好是 13 號 → 命中（靠 dom）
    assert cron_matches(*spec, dt=datetime(2026, 7, 13, 0, 0)) is True
    # 2026-07-17 是週五但不是 13 號 → 命中（靠 dow）
    assert cron_matches(*spec, dt=datetime(2026, 7, 17, 0, 0)) is True
    # 2026-07-14 週二、非 13 號 → 兩者都不符 → 不命中
    assert cron_matches(*spec, dt=datetime(2026, 7, 14, 0, 0)) is False


def test_only_dom_restricted_uses_and_semantics() -> None:
    # 只有日受限（星期為 *）→ 就照日判斷，不受星期影響
    spec = ("0", "0", "13", "*", "*")
    assert cron_matches(*spec, dt=datetime(2026, 7, 13, 0, 0)) is True   # 13 號
    assert cron_matches(*spec, dt=datetime(2026, 7, 14, 0, 0)) is False  # 非 13 號
