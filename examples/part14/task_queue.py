"""Part 14 ch21：一個迷你任務佇列，示範「為什麼需要獨立的任務佇列」。

對應章節：chapters/14-web/21-task-queue-why.md

重點概念（in-process BackgroundTasks 缺的東西）：
- enqueue / worker 分離：產生任務的人和執行任務的人解耦。
- 重試：暫時失敗自動重排隊，不是一次就丟。
- 死信佇列（dead-letter）：重試用盡的任務不會無聲消失，進死信待人工處理。
純標準庫；真實世界用 Celery + Redis/RabbitMQ 取代這裡的 deque。
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class Task:
    name: str
    payload: dict[str, object]
    max_retries: int = 3
    attempts: int = 0


@dataclass
class Worker:
    handlers: dict[str, Callable[[dict[str, object]], None]]
    queue: deque[Task] = field(default_factory=deque)
    dead_letter: list[Task] = field(default_factory=list)
    processed: list[str] = field(default_factory=list)

    def enqueue(self, task: Task) -> None:
        self.queue.append(task)

    def run_once(self) -> None:
        """取一個任務執行；失敗則重排隊，用盡重試進死信。"""
        if not self.queue:
            return
        task = self.queue.popleft()
        task.attempts += 1
        try:
            self.handlers[task.name](task.payload)
            self.processed.append(task.name)
        except Exception:  # noqa: BLE001 — 任務佇列刻意攔所有例外做重試/死信
            if task.attempts < task.max_retries:
                self.queue.append(task)      # 暫時失敗 → 重新排隊
            else:
                self.dead_letter.append(task)  # 用盡重試 → 死信，不無聲消失

    def drain(self) -> None:
        while self.queue:
            self.run_once()


def demo() -> None:
    calls = {"n": 0}

    def flaky(payload: dict[str, object]) -> None:
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("暫時失敗（例如對方 API 超時）")

    def always_fail(payload: dict[str, object]) -> None:
        raise RuntimeError("永久失敗（例如資料本身壞掉）")

    worker = Worker(handlers={"send_email": flaky, "broken": always_fail})
    worker.enqueue(Task("send_email", {"to": "a@b.c"}))
    worker.enqueue(Task("broken", {}, max_retries=2))
    worker.drain()
    print("成功處理:", worker.processed)
    print("進死信:", [(t.name, t.attempts) for t in worker.dead_letter])


if __name__ == "__main__":
    demo()
