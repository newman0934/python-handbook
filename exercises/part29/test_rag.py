"""Part 29 rag 測試。"""

from __future__ import annotations

from exercises.part29.rag import reciprocal_rank_fusion


def test_rrf_combines_rankings() -> None:
    r1 = ["a", "b", "c"]
    r2 = ["b", "a", "d"]
    result = reciprocal_rank_fusion([r1, r2])
    # a 與 b 各在一清單第 1、另一清單第 2,分數相同 → 並列前二
    assert set(result[:2]) == {"a", "b"}
    assert set(result) == {"a", "b", "c", "d"}


def test_rrf_single_ranking_preserves_order() -> None:
    assert reciprocal_rank_fusion([["x", "y", "z"]]) == ["x", "y", "z"]
