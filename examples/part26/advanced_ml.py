"""Part 26 進階機器學習範例:決策樹 / 集成 / 聚類 / PCA / 調參 /
不平衡 / 可解釋性 / 端到端。

用 scikit-learn + numpy,固定 random_state 確保可重現。
"""

from __future__ import annotations

import numpy as np
from scipy.stats import randint
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs, make_classification
from sklearn.decomposition import PCA
from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, recall_score, silhouette_score
from sklearn.model_selection import (
    GridSearchCV,
    RandomizedSearchCV,
    cross_val_score,
    train_test_split,
)
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


# ===== ch01 決策樹 =====
def tree_depth_scores(depth: int | None) -> tuple[float, float]:
    X, y = make_classification(
        n_samples=400, n_features=4, n_informative=3, n_redundant=0, random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    model = DecisionTreeClassifier(max_depth=depth, random_state=42).fit(X_train, y_train)
    return model.score(X_train, y_train), model.score(X_test, y_test)


# ===== ch02 集成 =====
def compare_ensembles() -> dict[str, float]:
    X, y = make_classification(n_samples=600, n_features=10, n_informative=6, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    models = {
        "tree": DecisionTreeClassifier(random_state=42),
        "forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "boosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
    }
    result = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        result[name] = round(model.score(X_test, y_test), 3)
    return result


# ===== ch03 聚類 =====
def kmeans_inertia(k: int) -> float:
    X, _ = make_blobs(n_samples=300, centers=3, cluster_std=0.8, random_state=42)
    return float(KMeans(n_clusters=k, n_init=10, random_state=42).fit(X).inertia_)


def best_k_by_silhouette(k_range: range) -> int:
    X, _ = make_blobs(n_samples=300, centers=3, cluster_std=0.8, random_state=42)
    best_k, best_score = 2, -1.0
    for k in k_range:
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
        score = silhouette_score(X, labels)
        if score > best_score:
            best_score, best_k = score, k
    return best_k


# ===== ch04 PCA =====
def pca_explained_variance(n_components: int) -> float:
    X, _ = make_classification(n_samples=200, n_features=6, n_informative=3, random_state=42)
    X_scaled = StandardScaler().fit_transform(X)
    pca = PCA(n_components=n_components).fit(X_scaled)
    return float(pca.explained_variance_ratio_.sum())


def pca_dims_for_variance(variance: float) -> int:
    X, _ = make_classification(n_samples=200, n_features=6, n_informative=3, random_state=42)
    X_scaled = StandardScaler().fit_transform(X)
    return int(PCA(n_components=variance).fit(X_scaled).n_components_)


# ===== ch05 調參 =====
def grid_search_rf() -> tuple[dict[str, object], float]:
    X, y = make_classification(n_samples=400, n_features=8, random_state=42)
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    gs = GridSearchCV(
        RandomForestClassifier(random_state=42),
        {"n_estimators": [50, 100], "max_depth": [3, 5, None]},
        cv=5,
        scoring="f1",
    )
    gs.fit(X_train, y_train)
    return gs.best_params_, round(gs.best_score_, 3)


def random_search_rf() -> float:
    X, y = make_classification(n_samples=400, n_features=8, random_state=42)
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    rs = RandomizedSearchCV(
        RandomForestClassifier(random_state=42),
        {"n_estimators": randint(50, 200), "max_depth": [3, 5, 7, None]},
        n_iter=8,
        cv=5,
        scoring="f1",
        random_state=42,
    )
    rs.fit(X_train, y_train)
    return round(float(rs.best_score_), 3)


# ===== ch06 不平衡 =====
def imbalance_recall(use_class_weight: bool) -> float:
    X, y = make_classification(
        n_samples=2000, n_features=10, n_informative=5, weights=[0.95, 0.05], random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    cw = "balanced" if use_class_weight else None
    model = LogisticRegression(max_iter=1000, class_weight=cw, random_state=42).fit(
        X_train, y_train
    )
    return round(float(recall_score(y_test, model.predict(X_test))), 3)


# ===== ch07 可解釋性 =====
def permutation_top_features(n_top: int) -> list[int]:
    X, y = make_classification(
        n_samples=500, n_features=5, n_informative=3, n_redundant=0, shuffle=False, random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    rf = RandomForestClassifier(n_estimators=100, random_state=42).fit(X_train, y_train)
    perm = permutation_importance(rf, X_test, y_test, n_repeats=10, random_state=42)
    return [int(i) for i in np.argsort(perm.importances_mean)[::-1][:n_top]]


# ===== ch08 端到端 =====
def advanced_pipeline() -> dict[str, float]:
    X, y = make_classification(
        n_samples=800, n_features=10, n_informative=6, weights=[0.7, 0.3], random_state=42
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    # 選拔:比較集成
    forest_cv = cross_val_score(
        RandomForestClassifier(n_estimators=100, class_weight="balanced", random_state=42),
        X_train,
        y_train,
        cv=5,
        scoring="f1",
    ).mean()
    # 調參
    gs = GridSearchCV(
        RandomForestClassifier(class_weight="balanced", random_state=42),
        {"n_estimators": [100, 200], "max_depth": [5, 10, None]},
        cv=5,
        scoring="f1",
    )
    gs.fit(X_train, y_train)
    test_f1 = f1_score(y_test, gs.best_estimator_.predict(X_test))
    return {"forest_cv_f1": round(float(forest_cv), 3), "test_f1": round(float(test_f1), 3)}
