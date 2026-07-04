"""Part 26 練習:評估指標(承 進階 ML:precision/recall)。

實作 precision_recall:用 sklearn.metrics 回傳 (precision, recall)。
提示:precision = TP/(TP+FP)、recall = TP/(TP+FN)。
"""

from __future__ import annotations


def precision_recall(y_true: list[int], y_pred: list[int]) -> tuple[float, float]:
    """回傳 (precision, recall)(正類為 1)。"""
    raise NotImplementedError("實作我!")
