"""Part 26 metrics 測試。"""

from __future__ import annotations

import pytest

from solutions.part26.metrics import precision_recall


def test_precision_recall() -> None:
    # TP=2, FP=1, FN=1 -> precision=2/3, recall=2/3
    y_true = [1, 1, 0, 0, 1]
    y_pred = [1, 0, 0, 1, 1]
    precision, recall = precision_recall(y_true, y_pred)
    assert precision == pytest.approx(2 / 3)
    assert recall == pytest.approx(2 / 3)


def test_perfect() -> None:
    assert precision_recall([1, 0, 1], [1, 0, 1]) == (1.0, 1.0)
