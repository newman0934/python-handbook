"""Part 28 練習:餘弦相似度與語意檢索(承 06-embeddings-semantic-search)。

實作 cosine_similarity(dot / (norm*norm))與 top_k_similar
(回傳最相似前 k 個文件的索引,由高到低)。
"""

from __future__ import annotations

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """回傳兩向量的餘弦相似度。"""
    raise NotImplementedError("實作我!")


def top_k_similar(query: np.ndarray, docs: list[np.ndarray], k: int) -> list[int]:
    """回傳與 query 最相似的前 k 個文件『索引』(由高到低)。"""
    raise NotImplementedError("實作我!")
