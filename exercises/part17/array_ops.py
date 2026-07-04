"""Part 17 練習:numpy 陣列運算(承 numpy 章)。

實作 normalize(Min-Max 到 [0,1])與 zscore(標準化為平均 0、標準差 1)。
提示:用向量化運算 a.min()/a.max()/a.mean()/a.std(),不要寫迴圈。
"""

from __future__ import annotations

import numpy as np


def normalize(a: np.ndarray) -> np.ndarray:
    """Min-Max 正規化到 [0, 1]。"""
    raise NotImplementedError("實作我!")


def zscore(a: np.ndarray) -> np.ndarray:
    """標準化為平均 0、標準差 1(z-score)。"""
    raise NotImplementedError("實作我!")
