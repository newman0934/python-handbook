"""領域例外(與 HTTP 解耦;由 API 層轉成對應狀態碼)。"""

from __future__ import annotations


class TaskNotFoundError(Exception):
    """找不到指定任務。"""

    def __init__(self, task_id: int) -> None:
        super().__init__(f"task {task_id} not found")
        self.task_id = task_id
