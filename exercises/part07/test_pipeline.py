"""Part 7 pipeline 測試。"""

from __future__ import annotations

import pytest

from exercises.part07.pipeline import chunked, running_max


def test_chunked() -> None:
    assert [list(c) for c in chunked([1, 2, 3, 4, 5], 2)] == [[1, 2], [3, 4], [5]]


def test_chunked_invalid() -> None:
    with pytest.raises(ValueError):
        list(chunked([1], 0))


def test_running_max() -> None:
    assert list(running_max([1, 3, 2, 5, 4])) == [1, 3, 3, 5, 5]
