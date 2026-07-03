"""Part 25 機器學習基礎範例:學閾值 / train-test split / 特徵工程 /
線性回歸 / 邏輯回歸 / 評估指標 / 過擬合正則化 CV / 端到端 Pipeline。

用 scikit-learn + numpy,固定 random_state 確保可重現。
"""

from __future__ import annotations

import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (
    f1_score,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, PolynomialFeatures, StandardScaler


# ===== ch01 從資料學閾值 =====
def learn_threshold(features: list[float], labels: list[int]) -> tuple[float, float]:
    best_threshold, best_acc = 0.0, -1.0
    for t in sorted(set(features)):
        preds = [1 if x >= t else 0 for x in features]
        acc = sum(p == y for p, y in zip(preds, labels, strict=True)) / len(labels)
        if acc > best_acc:
            best_acc, best_threshold = acc, t
    return best_threshold, best_acc


# ===== ch02 工作流:正確 split + scale =====
def train_with_proper_split() -> tuple[float, float]:
    X, y = make_classification(n_samples=200, n_features=5, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)  # fit 只在 train
    X_test_s = scaler.transform(X_test)  # test 只 transform
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train_s, y_train)
    return model.score(X_train_s, y_train), model.score(X_test_s, y_test)


# ===== ch03 特徵工程 =====
def standardize(values: np.ndarray) -> np.ndarray:
    return np.asarray(StandardScaler().fit_transform(values))


def one_hot(categories: list[str]) -> np.ndarray:
    enc = OneHotEncoder(sparse_output=False)
    arr = np.array(categories).reshape(-1, 1)
    return np.asarray(enc.fit_transform(arr))


# ===== ch04 線性回歸 =====
def fit_linear_regression() -> tuple[list[float], float, float]:
    """回 (係數, 截距, test R2);資料由 50*area + 30*rooms + 100 生成。"""
    rng = np.random.default_rng(42)
    n = 200
    area = rng.uniform(10, 50, n)
    rooms = rng.integers(1, 5, n)
    price = 50 * area + 30 * rooms + 100 + rng.normal(0, 20, n)
    X = np.column_stack([area, rooms])
    X_train, X_test, y_train, y_test = train_test_split(X, price, test_size=0.3, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)
    return list(model.coef_), float(model.intercept_), r2_score(y_test, model.predict(X_test))


# ===== ch05 邏輯回歸 =====
def sigmoid(z: float) -> float:
    return float(1 / (1 + np.exp(-z)))


def classify_with_threshold(proba: list[float], threshold: float) -> list[int]:
    return [1 if p >= threshold else 0 for p in proba]


# ===== ch06 評估指標 =====
def evaluate_classification(y_true: list[int], y_pred: list[int]) -> dict[str, float]:
    return {
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 3),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 3),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 3),
    }


# ===== ch07 過擬合 / 正則化 / CV =====
def polynomial_fit(degree: int, alpha: float = 0.0) -> tuple[float, float]:
    """回 (train R2, test R2);degree 越高越易過擬合,alpha>0 加 Ridge 正則化。"""
    rng = np.random.default_rng(0)
    X = np.sort(rng.uniform(0, 1, 20)).reshape(-1, 1)
    y = np.sin(2 * np.pi * X).ravel() + rng.normal(0, 0.15, 20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, random_state=0)
    est = LinearRegression() if alpha == 0 else Ridge(alpha=alpha)
    model = make_pipeline(PolynomialFeatures(degree), est)
    model.fit(X_train, y_train)
    return (
        r2_score(y_train, model.predict(X_train)),
        r2_score(y_test, model.predict(X_test)),
    )


def cv_score(degree: int) -> tuple[float, float]:
    rng = np.random.default_rng(0)
    X = np.sort(rng.uniform(0, 1, 20)).reshape(-1, 1)
    y = np.sin(2 * np.pi * X).ravel() + rng.normal(0, 0.15, 20)
    kf = KFold(n_splits=5, shuffle=True, random_state=0)
    scores = cross_val_score(
        make_pipeline(PolynomialFeatures(degree), LinearRegression()), X, y, cv=kf, scoring="r2"
    )
    return float(scores.mean()), float(scores.std())


# ===== ch08 端到端 Pipeline =====
def end_to_end_pipeline() -> dict[str, float]:
    X, y = make_classification(
        n_samples=500, n_features=8, n_informative=5, weights=[0.7, 0.3], random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
    best_c, best_score = 1.0, -1.0
    for c in (0.01, 0.1, 1, 10):
        pipe.set_params(clf__C=c)
        score = cross_val_score(pipe, X_train, y_train, cv=5, scoring="f1").mean()
        if score > best_score:
            best_score, best_c = score, c
    pipe.set_params(clf__C=best_c).fit(X_train, y_train)
    proba = pipe.predict_proba(X_test)[:, 1]
    return {"best_C": best_c, "test_auc": round(roc_auc_score(y_test, proba), 3)}
