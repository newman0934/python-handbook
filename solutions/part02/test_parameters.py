"""Part 2 parameters 測試。"""

from __future__ import annotations

from solutions.part02.parameters import merge_config, running_total


def test_running_total() -> None:
    assert running_total(1, 2, 3) == [1, 3, 6]


def test_running_total_empty() -> None:
    assert running_total() == []


def test_merge_config_overrides() -> None:
    assert merge_config({"a": 1, "b": 2}, b=3, c=4) == {"a": 1, "b": 3, "c": 4}


def test_merge_config_does_not_mutate_base() -> None:
    base = {"x": 1}
    merge_config(base, y=2)
    assert base == {"x": 1}
