"""Part 26 練習:評估指標(承 進階 ML:precision/recall)。"""

from __future__ import annotations

from sklearn.metrics import precision_score, recall_score


def precision_recall(y_true: list[int], y_pred: list[int]) -> tuple[float, float]:
    """回傳 (precision, recall)(正類為 1)。"""
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    return (precision, recall)
