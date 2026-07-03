"""Part 17（補充）ML 與 polars 範例的驗證測試。"""

from __future__ import annotations

from examples.part17.ml_polars import (
    revenue_by_city,
    revenue_by_city_lazy_filtered,
    train_and_evaluate_iris,
)


# --- scikit-learn（見 08）---
def test_train_iris_deterministic() -> None:
    n_train, n_test, accuracy = train_and_evaluate_iris()
    assert n_train == 105  # 70% of 150
    assert n_test == 45  # 30%
    assert accuracy == 1.0  # 固定 seed → 準確率 100%


# --- polars（見 09）---
def test_polars_eager_groupby() -> None:
    assert revenue_by_city() == [
        {"city": "Osaka", "total": 80},
        {"city": "Taipei", "total": 250},
        {"city": "Tokyo", "total": 500},
    ]


def test_polars_lazy_filtered() -> None:
    # 只算 amount>100：Taipei 只剩 150、Tokyo 500，Osaka(80) 被排除
    assert revenue_by_city_lazy_filtered() == [
        {"city": "Taipei", "total": 150},
        {"city": "Tokyo", "total": 500},
    ]
