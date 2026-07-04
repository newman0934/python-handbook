"""Part 29 練習:RRF 融合(承 03-hybrid-retrieval-rerank)。"""

from __future__ import annotations


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    """倒數排名融合:對每個排名清單,文件 doc 在名次 rank(0-based)得分 1/(k+rank+1),
    加總後由高到低排序回傳文件清單。"""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=lambda d: scores[d], reverse=True)
