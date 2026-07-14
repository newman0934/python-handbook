"""Part 14 ch23：一個迷你 cron 運算式比對器。

對應章節：chapters/14-web/23-scheduling.md

排程器（Celery beat / APScheduler / 系統 cron）的核心邏輯，就是「現在這個時間，
符合這條 cron 規則嗎？符合就派工」。這裡把那個判斷抽成純函式，可獨立測試。
支援 *, 具體數字, a-b 範圍, a,b,c 列舉, */n 步進。
"""

from __future__ import annotations

from datetime import datetime


def _match_field(spec: str, value: int, low: int) -> bool:
    """單一 cron 欄位是否匹配 value。low 是該欄位的最小值（用於 */n 對齊）。"""
    for part in spec.split(","):
        if part == "*":
            return True
        if part.startswith("*/"):
            step = int(part[2:])
            if step > 0 and (value - low) % step == 0:
                return True
        elif "-" in part:
            start, end = part.split("-")
            if int(start) <= value <= int(end):
                return True
        elif part.isdigit() and int(part) == value:
            return True
    return False


def cron_matches(
    minute: str, hour: str, dom: str, month: str, dow: str, dt: datetime
) -> bool:
    """五欄位 cron（分 時 日 月 週）是否匹配 dt。dow：0=週日…6=週六。"""
    return (
        _match_field(minute, dt.minute, 0)
        and _match_field(hour, dt.hour, 0)
        and _match_field(dom, dt.day, 1)
        and _match_field(month, dt.month, 1)
        and _match_field(dow, dt.isoweekday() % 7, 0)
    )


def demo() -> None:
    daily_3am = ("0", "3", "*", "*", "*")
    print("每天 03:00 —— 03:00 符合?",
          cron_matches(*daily_3am, dt=datetime(2026, 7, 14, 3, 0)))
    print("每天 03:00 —— 03:01 符合?",
          cron_matches(*daily_3am, dt=datetime(2026, 7, 14, 3, 1)))
    every_15 = ("*/15", "*", "*", "*", "*")
    print("每 15 分 —— 09:30 符合?",
          cron_matches(*every_15, dt=datetime(2026, 7, 14, 9, 30)))
    print("每 15 分 —— 09:31 符合?",
          cron_matches(*every_15, dt=datetime(2026, 7, 14, 9, 31)))


if __name__ == "__main__":
    demo()
