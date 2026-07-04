"""Part 6 context_manager 測試。"""

from __future__ import annotations

import pytest

from solutions.part06.context_manager import Bracket


def test_enter_exit_order() -> None:
    log: list[str] = []
    with Bracket(log, "a"):
        log.append("body")
    assert log == ["enter a", "body", "exit a"]


def test_exit_runs_on_exception() -> None:
    log: list[str] = []
    with pytest.raises(ValueError):  # noqa: SIM117
        with Bracket(log, "x"):
            raise ValueError("boom")
    assert log == ["enter x", "exit x"]  # exit 仍被記錄
