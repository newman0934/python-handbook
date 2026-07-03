"""Part 13（補充）CLI 範例的驗證測試。"""

from __future__ import annotations

import contextlib
import io

import pytest

from examples.part13.cli import run


def test_hello_basic() -> None:
    assert run(["hello", "Alice"]) == "Hello, Alice!"


def test_hello_count_and_upper() -> None:
    assert run(["hello", "Bob", "-c", "2", "--upper"]) == "HELLO, BOB!\nHELLO, BOB!"


def test_bye_subcommand() -> None:
    assert run(["bye", "Carol"]) == "Bye, Carol!"


def test_invalid_int_exits() -> None:
    # argparse 對非整數 --count 自動報錯並以非 0 退出
    with pytest.raises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
        run(["hello", "Bob", "-c", "notanumber"])
