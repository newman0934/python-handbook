"""Part 0 ch08：攔截 SIGTERM，走優雅關閉。

對應章節：chapters/00-backend-foundations/08-signals-lifecycle.md
"""

from __future__ import annotations

import signal
from types import FrameType


class Server:
    """模擬一個服務：收到 SIGTERM 走優雅關閉，不是直接斷電。"""

    def __init__(self) -> None:
        self.running = True
        self.shutdown_log: list[str] = []

    def handle_sigterm(self, signum: int, frame: FrameType | None) -> None:
        """SIGTERM handler：準備打烊的 SOP（可攔截、應攔截）。"""
        name = signal.Signals(signum).name
        self.shutdown_log.append(f"收到 {name}（訊號 {signum}）")
        self.shutdown_log.append("1. 停止接受新請求")
        self.shutdown_log.append("2. 等在途請求做完")
        self.shutdown_log.append("3. 關閉 DB 連線、釋放資源")
        self.running = False


def run_and_trigger() -> Server:
    """註冊 handler、對自己發 SIGTERM，回傳收尾後的 server 狀態。"""
    server = Server()
    original = signal.getsignal(signal.SIGTERM)
    signal.signal(signal.SIGTERM, server.handle_sigterm)
    try:
        signal.raise_signal(signal.SIGTERM)
    finally:
        signal.signal(signal.SIGTERM, original)  # 還原，別影響其他測試
    return server
