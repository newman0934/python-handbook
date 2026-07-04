"""Part 11 text_re 測試。"""

from __future__ import annotations

from exercises.part11.text_re import extract_numbers, slugify


def test_extract_numbers() -> None:
    assert extract_numbers("a1 b22 c-3") == [1, 22, -3]


def test_extract_numbers_none() -> None:
    assert extract_numbers("no digits") == []


def test_slugify() -> None:
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_trims_dashes() -> None:
    assert slugify("  Python 3.12  ") == "python-3-12"
