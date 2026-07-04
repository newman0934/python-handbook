"""Part 9 練習:執行緒安全計數器(承 04-thread-sync)。

實作 SafeCounter(用 threading.Lock 保護 increment)與 run_incrementers。
正確實作下,多執行緒併發遞增的最終值應精確 = threads * per_thread。
"""

from __future__ import annotations


class SafeCounter:
    def __init__(self) -> None:
        raise NotImplementedError("實作我!")

    def increment(self) -> None:
        raise NotImplementedError("實作我!")

    @property
    def value(self) -> int:
        raise NotImplementedError("實作我!")


def run_incrementers(counter: SafeCounter, threads: int, per_thread: int) -> int:
    """開 threads 條執行緒,各 increment per_thread 次;回傳最終值。"""
    raise NotImplementedError("實作我!")
