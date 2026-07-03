"""Part 17（補充）機器學習入門(scikit-learn) 與 polars 高效 DataFrame 範例。"""

from __future__ import annotations

import polars as pl
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier


# ===== scikit-learn：監督式學習流程（見 08）=====
def train_and_evaluate_iris() -> tuple[int, int, float]:
    """訓練決策樹分類鳶尾花，回 (訓練數, 測試數, 測試集準確率)。固定 seed 可重現。"""
    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    model = DecisionTreeClassifier(max_depth=3, random_state=42)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    accuracy = float(accuracy_score(y_test, predictions))
    return len(X_train), len(X_test), accuracy


# ===== polars：eager 與 lazy 查詢（見 09）=====
def _sample_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "city": ["Taipei", "Tokyo", "Taipei", "Osaka", "Tokyo"],
            "amount": [100, 200, 150, 80, 300],
        }
    )


def revenue_by_city() -> list[dict[str, object]]:
    """eager 分組聚合，回 ASCII 安全的 dict list。"""
    df = _sample_df()
    grouped = df.group_by("city").agg(pl.col("amount").sum().alias("total")).sort("city")
    return grouped.to_dicts()


def revenue_by_city_lazy_filtered() -> list[dict[str, object]]:
    """lazy 查詢：只算 amount>100 的，collect 時優化執行。"""
    result = (
        _sample_df()
        .lazy()
        .filter(pl.col("amount") > 100)
        .group_by("city")
        .agg(pl.col("amount").sum().alias("total"))
        .sort("city")
        .collect()
    )
    return result.to_dicts()
