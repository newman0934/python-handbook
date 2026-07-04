"""Part 29 練習:RRF 融合(承 03-hybrid-retrieval-rerank)。

實作 reciprocal_rank_fusion:文件在某清單名次 rank(0-based)得分 1/(k+rank+1),
跨清單加總後由高到低排序。這是混合檢索融合多路結果的常用法。
"""

from __future__ import annotations


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    """倒數排名融合,回傳融合後由高到低的文件清單。"""
    raise NotImplementedError("實作我!")
