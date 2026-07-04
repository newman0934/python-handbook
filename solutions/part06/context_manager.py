"""Part 6 練習:context manager(承 06-context-manager)。"""

from __future__ import annotations

from types import TracebackType


class Bracket:
    """進出區塊時往 log 追加標記,離開時即使發生例外也要記錄。"""

    def __init__(self, log: list[str], name: str) -> None:
        self.log = log
        self.name = name

    def __enter__(self) -> Bracket:
        self.log.append(f"enter {self.name}")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.log.append(f"exit {self.name}")
