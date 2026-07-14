"""Part 0 ch06：執行緒共享記憶體、行程各自記憶體。

對應章節：chapters/00-backend-foundations/06-process-thread.md
"""

from __future__ import annotations

import multiprocessing
import os
import threading


def collect_via_threads(n: int) -> list[int]:
    """n 個執行緒各 append 一個值到「共享」的 list → 證明共享記憶體。"""
    shared: list[int] = []
    threads = [threading.Thread(target=shared.append, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return shared


def _child(queue: multiprocessing.Queue[dict[str, object]]) -> None:
    """子行程：回報自己的 PID 與「自己的」list。"""
    local = [999, 123]
    queue.put({"child_pid": os.getpid(), "child_list": local})


def child_report() -> dict[str, object]:
    """啟動一個子行程，取回它的 PID 與 list（證明記憶體隔離）。"""
    queue: multiprocessing.Queue[dict[str, object]] = multiprocessing.Queue()
    proc = multiprocessing.Process(target=_child, args=(queue,))
    proc.start()
    result = queue.get()
    proc.join()
    return result
