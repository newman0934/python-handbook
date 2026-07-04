"""Part 17 array_ops 測試。"""

from __future__ import annotations

import numpy as np

from solutions.part17.array_ops import normalize, zscore


def test_normalize() -> None:
    result = normalize(np.array([0.0, 5.0, 10.0]))
    assert np.allclose(result, [0.0, 0.5, 1.0])


def test_zscore_mean_std() -> None:
    result = zscore(np.array([1.0, 2.0, 3.0, 4.0]))
    assert np.allclose(result.mean(), 0.0)
    assert np.allclose(result.std(), 1.0)
