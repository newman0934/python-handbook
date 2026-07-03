"""Part 12（補充）屬性測試範例（Hypothesis）。

Hypothesis 自動生成大量輸入驗證「應永遠成立的性質」。
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from examples.part12.property_based import rle_decode, rle_encode


# 性質 1：往返——任何字串 encode 再 decode 應還原
@given(st.text())
def test_rle_roundtrip(s: str) -> None:
    assert rle_decode(rle_encode(s)) == s


# 性質 2：不變量——sorted 結果永遠遞增
@given(st.lists(st.integers()))
def test_sorted_is_ordered(xs: list[int]) -> None:
    result = sorted(xs)
    assert all(result[i] <= result[i + 1] for i in range(len(result) - 1))


# 性質 3：冪等——排序兩次等於排序一次
@given(st.lists(st.integers()))
def test_sort_idempotent(xs: list[int]) -> None:
    assert sorted(sorted(xs)) == sorted(xs)


# 性質 4：與內建對比（oracle）——自製 max 對任何非空列表都應等於 max
@given(st.lists(st.integers(), min_size=1))
def test_my_max_matches_builtin(xs: list[int]) -> None:
    m = xs[0]
    for x in xs[1:]:
        if x > m:
            m = x
    assert m == max(xs)
