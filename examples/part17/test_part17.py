"""Part 17 範例的驗證測試。

執行：pytest examples/part17
"""

from __future__ import annotations

from pathlib import Path

import pytest

from examples.part17.data_science import (
    broadcast_column_bonus,
    clean_people,
    pass_rate,
    revenue_by_city,
    revenue_by_country,
    save_bar_chart,
    scale_and_shift,
)


# --- numpy 向量化與廣播 ---
def test_scale_and_shift() -> None:
    assert scale_and_shift([1.0, 2.0, 3.0], 2.0, 1.0) == [3.0, 5.0, 7.0]


def test_broadcast_column_bonus() -> None:
    # 每列加不同 bonus：第一列 +10、第二列 +20
    assert broadcast_column_bonus([[1, 2, 3], [4, 5, 6]], [10, 20]) == [
        [11, 12, 13],
        [24, 25, 26],
    ]


@pytest.mark.parametrize(
    ("scores", "threshold", "expected"),
    [
        ([55, 90, 72, 40, 88], 60, 0.6),
        ([100, 100], 60, 1.0),
        ([10, 20], 60, 0.0),
    ],
)
def test_pass_rate(scores: list[int], threshold: int, expected: float) -> None:
    assert pass_rate(scores, threshold) == pytest.approx(expected)


# --- pandas groupby / merge ---
_ORDERS: list[dict[str, object]] = [
    {"order_id": 1, "city": "Taipei", "amount": 100},
    {"order_id": 2, "city": "Tokyo", "amount": 200},
    {"order_id": 3, "city": "Taipei", "amount": 150},
    {"order_id": 4, "city": "Osaka", "amount": 80},
    {"order_id": 5, "city": "Tokyo", "amount": 300},
]


def test_revenue_by_city() -> None:
    assert revenue_by_city(_ORDERS) == {"Osaka": 80, "Taipei": 250, "Tokyo": 500}


def test_revenue_by_country() -> None:
    mapping = {"Taipei": "Taiwan", "Tokyo": "Japan", "Osaka": "Japan"}
    assert revenue_by_country(_ORDERS, mapping) == {"Japan": 580, "Taiwan": 250}


# --- 資料清理 ---
def test_clean_people() -> None:
    rows: list[dict[str, object]] = [
        {"name": "Alice", "age": "30"},
        {"name": "Bob", "age": "25"},
        {"name": " Carol ", "age": None},  # 缺失 → 中位數填補
        {"name": "Bob", "age": "25"},  # 重複
        {"name": "Eve", "age": "abc"},  # 爛值 → NaN → 填補
    ]
    df = clean_people(rows)
    # 去重後 4 列（兩筆 Bob 合一）
    assert len(df) == 4
    # 字串去空白
    assert df["name"].tolist() == ["Alice", "Bob", "Carol", "Eve"]
    # 無缺失
    assert int(df["age"].isna().sum()) == 0
    # 缺失/爛值以中位數(25)填補
    assert df.loc[df["name"] == "Carol", "age"].iloc[0] == 25.0
    assert df.loc[df["name"] == "Eve", "age"].iloc[0] == 25.0


# --- 視覺化 ---
def test_save_bar_chart(tmp_path: Path) -> None:
    out = tmp_path / "chart.png"
    assert save_bar_chart(["A", "B", "C"], [1.0, 2.0, 3.0], out) is True
    assert out.exists()
