"""Part 27 練習:神經網路基本運算(承 numpy 從零打造)。

實作 sigmoid、relu、dense(x@w+b)。用向量化 numpy 運算。
"""

from __future__ import annotations

import numpy as np


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Sigmoid 激活:1/(1+e^-x)。"""
    raise NotImplementedError("實作我!")


def relu(x: np.ndarray) -> np.ndarray:
    """ReLU 激活:max(0, x)。"""
    raise NotImplementedError("實作我!")


def dense(x: np.ndarray, w: np.ndarray, b: np.ndarray) -> np.ndarray:
    """全連接層:x @ w + b。"""
    raise NotImplementedError("實作我!")
