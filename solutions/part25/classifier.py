"""Part 25 練習:訓練分類器(承 ML 基礎)。"""

from __future__ import annotations

from sklearn.linear_model import LogisticRegression


def train_and_accuracy(features: list[list[float]], labels: list[int]) -> float:
    """訓練 LogisticRegression 並回傳在訓練資料上的準確率(0~1)。"""
    model = LogisticRegression()
    model.fit(features, labels)
    predictions = model.predict(features)
    correct = sum(1 for p, y in zip(predictions, labels, strict=True) if int(p) == y)
    return correct / len(labels)
