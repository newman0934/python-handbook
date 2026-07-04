"""Part 17 練習:numpy 陣列運算(承 numpy 章)。"""

from __future__ import annotations

import numpy as np


def normalize(a: np.ndarray) -> np.ndarray:
    """Min-Max 正規化到 [0, 1]。"""
    lo = a.min()
    hi = a.max()
    return np.asarray((a - lo) / (hi - lo))


def zscore(a: np.ndarray) -> np.ndarray:
    """標準化為平均 0、標準差 1(z-score)。"""
    return np.asarray((a - a.mean()) / a.std())
