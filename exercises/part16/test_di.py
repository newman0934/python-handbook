"""Part 16 di 測試。"""

from __future__ import annotations

from exercises.part16.di import NotificationService


class FakeNotifier:
    """測試替身:記錄所有送出的訊息。"""

    def __init__(self) -> None:
        self.sent: list[str] = []

    def send(self, message: str) -> None:
        self.sent.append(message)


def test_notify_all_uses_injected_notifier() -> None:
    fake = FakeNotifier()
    service = NotificationService(fake)
    service.notify_all(["a", "b"])
    assert fake.sent == ["[INFO] a", "[INFO] b"]


def test_notify_all_empty() -> None:
    fake = FakeNotifier()
    NotificationService(fake).notify_all([])
    assert fake.sent == []
