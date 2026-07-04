"""Part 4 stack 測試。"""

from __future__ import annotations

import pytest

from exercises.part04.stack import Stack


def test_lifo() -> None:
    s = Stack()
    s.push(1)
    s.push(2)
    s.push(3)
    assert [s.pop(), s.pop(), s.pop()] == [3, 2, 1]


def test_peek_and_len() -> None:
    s = Stack()
    s.push(10)
    s.push(20)
    assert s.peek() == 20
    assert len(s) == 2
    assert s.peek() == 20  # peek 不移除


def test_is_empty() -> None:
    s = Stack()
    assert s.is_empty()
    s.push(1)
    assert not s.is_empty()


def test_pop_empty_raises() -> None:
    with pytest.raises(IndexError):
        Stack().pop()
