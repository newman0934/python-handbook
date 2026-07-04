"""Part 28 embeddings 測試。"""

from __future__ import annotations

import numpy as np
import pytest

from exercises.part28.embeddings import cosine_similarity, top_k_similar


def test_cosine_identical() -> None:
    v = np.array([1.0, 2.0, 3.0])
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_orthogonal() -> None:
    assert cosine_similarity(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == pytest.approx(0.0)


def test_top_k_similar() -> None:
    query = np.array([1.0, 0.0])
    docs = [np.array([1.0, 0.0]), np.array([0.0, 1.0]), np.array([0.9, 0.1])]
    assert top_k_similar(query, docs, 2) == [0, 2]
