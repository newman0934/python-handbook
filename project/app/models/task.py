"""資料模型層:pydantic schema 與領域實體(承 Part 14 pydantic)。"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """建立任務的輸入(title 不可為空)。"""

    title: str = Field(min_length=1, max_length=200)
    description: str = ""


class TaskUpdate(BaseModel):
    """部分更新任務(全部可選;None 表不更動該欄)。"""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    done: bool | None = None


class Task(BaseModel):
    """任務領域實體,同時作為 API 回應模型。"""

    id: int
    title: str
    description: str
    done: bool
    created_at: datetime

    @staticmethod
    def new(task_id: int, title: str, description: str) -> Task:
        return Task(
            id=task_id,
            title=title,
            description=description,
            done=False,
            created_at=datetime.now(UTC),
        )
