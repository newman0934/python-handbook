"""Part 16 練習:依賴注入 + Protocol(承 03-dependency-injection)。"""

from __future__ import annotations

from typing import Protocol


class Notifier(Protocol):
    """通知器介面。"""

    def send(self, message: str) -> None: ...


class NotificationService:
    """依賴注入:建構時接收 Notifier,不自己建立(可替換、可測)。"""

    def __init__(self, notifier: Notifier) -> None:
        self._notifier = notifier

    def notify_all(self, messages: list[str]) -> None:
        for m in messages:
            self._notifier.send(f"[INFO] {m}")
