"""Part 27 練習:神經網路基本運算(承 numpy 從零打造)。"""

from __future__ import annotations

import numpy as np


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Sigmoid 激活:1/(1+e^-x)。"""
    return np.asarray(1.0 / (1.0 + np.exp(-x)))


def relu(x: np.ndarray) -> np.ndarray:
    """ReLU 激活:max(0, x)。"""
    return np.asarray(np.maximum(0.0, x))


def dense(x: np.ndarray, w: np.ndarray, b: np.ndarray) -> np.ndarray:
    """全連接層:x @ w + b。"""
    return np.asarray(x @ w + b)
