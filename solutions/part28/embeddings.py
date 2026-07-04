"""Part 28 練習:餘弦相似度與語意檢索(承 06-embeddings-semantic-search)。"""

from __future__ import annotations

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """回傳兩向量的餘弦相似度。"""
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b)) / denom


def top_k_similar(query: np.ndarray, docs: list[np.ndarray], k: int) -> list[int]:
    """回傳與 query 最相似的前 k 個文件『索引』(由高到低)。"""
    sims = [cosine_similarity(query, d) for d in docs]
    return sorted(range(len(docs)), key=lambda i: sims[i], reverse=True)[:k]
