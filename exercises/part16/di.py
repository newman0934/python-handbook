"""Part 16 練習:依賴注入 + Protocol(承 03-dependency-injection)。

實作 NotificationService:建構子接收一個 Notifier(依賴注入),
notify_all 對每則訊息呼叫 notifier.send,並加上 "[INFO] " 前綴。
"""

from __future__ import annotations

from typing import Protocol


class Notifier(Protocol):
    def send(self, message: str) -> None: ...


class NotificationService:
    def __init__(self, notifier: Notifier) -> None:
        raise NotImplementedError("實作我!")

    def notify_all(self, messages: list[str]) -> None:
        raise NotImplementedError("實作我!")
