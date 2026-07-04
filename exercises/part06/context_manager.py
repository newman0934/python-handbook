"""Part 6 練習:context manager(承 06-context-manager)。

實作 Bracket:__enter__ 時往 log 加 "enter <name>",__exit__ 時加 "exit <name>"
(即使區塊內發生例外也要記錄 exit,且不吞例外)。
"""

from __future__ import annotations

from types import TracebackType


class Bracket:
    def __init__(self, log: list[str], name: str) -> None:
        self.log = log
        self.name = name

    def __enter__(self) -> Bracket:
        raise NotImplementedError("實作我!")

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        raise NotImplementedError("實作我!")
