"""Part 9 練習:執行緒安全計數器(承 04-thread-sync)。"""

from __future__ import annotations

import threading


class SafeCounter:
    """多執行緒可安全遞增的計數器(用 Lock 保護)。"""

    def __init__(self) -> None:
        self._value = 0
        self._lock = threading.Lock()

    def increment(self) -> None:
        with self._lock:
            self._value += 1

    @property
    def value(self) -> int:
        return self._value


def run_incrementers(counter: SafeCounter, threads: int, per_thread: int) -> int:
    """開 threads 條執行緒,各 increment per_thread 次;回傳最終值。"""

    def work() -> None:
        for _ in range(per_thread):
            counter.increment()

    workers = [threading.Thread(target=work) for _ in range(threads)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    return counter.value
