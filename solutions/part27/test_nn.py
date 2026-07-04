"""Part 27 nn 測試。"""

from __future__ import annotations

import numpy as np

from solutions.part27.nn import dense, relu, sigmoid


def test_sigmoid() -> None:
    assert np.allclose(sigmoid(np.array([0.0])), [0.5])


def test_relu() -> None:
    assert np.allclose(relu(np.array([-1.0, 0.0, 2.0])), [0.0, 0.0, 2.0])


def test_dense() -> None:
    x = np.array([[1.0, 2.0]])
    w = np.array([[1.0], [1.0]])
    b = np.array([0.5])
    assert np.allclose(dense(x, w, b), [[3.5]])
