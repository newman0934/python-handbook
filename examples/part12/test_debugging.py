"""Part 12（補充）除錯範例的驗證測試。"""

from __future__ import annotations

import pytest

from examples.part12.debugging import (
    buggy_average,
    correct_average,
    last_traceback_line,
)


def test_bug_vs_correct() -> None:
    data = [10.0, 20.0, 30.0]
    assert correct_average(data) == 20.0
    assert buggy_average(data) == 15.0  # off-by-one：分母用了 len+1


def test_correct_average_empty_raises() -> None:
    with pytest.raises(ValueError, match="空序列"):
        correct_average([])


def test_last_traceback_line() -> None:
    try:
        correct_average([])
    except ValueError as exc:
        line = last_traceback_line(exc)
        assert line == "ValueError: 空序列無法算平均"
