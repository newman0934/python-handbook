"""Part 1 範例的驗證測試。

執行：pytest examples/part01
"""

import platform

import pytest

from examples.part01.env_info import env_summary
from examples.part01.greeting import greet
from examples.part01.word_count import top_words


@pytest.mark.parametrize(
    ("text", "n", "expected"),
    [
        ("the the the a a b", 1, [("the", 3)]),
        ("the the the a a b", 2, [("the", 3), ("a", 2)]),
        ("HELLO hello Hello", 1, [("hello", 3)]),  # 不分大小寫
    ],
)
def test_top_words(text: str, n: int, expected: list[tuple[str, int]]) -> None:
    assert top_words(text, n) == expected


def test_greet() -> None:
    assert greet("Alice") == "Hello, Alice!"


def test_env_summary_reports_this_interpreter() -> None:
    summary = env_summary()
    # 應與正在執行測試的直譯器一致
    assert summary["version"] == platform.python_version()
    assert summary["implementation"] == platform.python_implementation()
    assert summary["is_64bit"] in {"True", "False"}
