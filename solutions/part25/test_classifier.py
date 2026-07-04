"""Part 25 classifier 測試。"""

from __future__ import annotations

from solutions.part25.classifier import train_and_accuracy


def test_linearly_separable_perfect() -> None:
    features = [[0.0], [1.0], [2.0], [10.0], [11.0], [12.0]]
    labels = [0, 0, 0, 1, 1, 1]
    assert train_and_accuracy(features, labels) == 1.0
