"""Part 1 word_frequency 測試。"""

from __future__ import annotations

from exercises.part01.word_frequency import word_frequency


def test_counts_words() -> None:
    assert word_frequency("a b a c a b") == {"a": 3, "b": 2, "c": 1}


def test_case_insensitive() -> None:
    assert word_frequency("Hi hi HI") == {"hi": 3}


def test_extra_whitespace() -> None:
    assert word_frequency("  x   y  ") == {"x": 1, "y": 1}


def test_empty() -> None:
    assert word_frequency("") == {}
