"""Part 26 範例測試:決策樹 / 集成 / 聚類 / PCA / 調參 / 不平衡 /
可解釋性 / 端到端。"""

from __future__ import annotations

from examples.part26.advanced_ml import (
    advanced_pipeline,
    best_k_by_silhouette,
    compare_ensembles,
    grid_search_rf,
    imbalance_recall,
    kmeans_inertia,
    pca_dims_for_variance,
    pca_explained_variance,
    permutation_top_features,
    random_search_rf,
    tree_depth_scores,
)


# ===== ch01 決策樹 =====
def test_unlimited_tree_overfits() -> None:
    train_none, test_none = tree_depth_scores(None)
    train_3, _ = tree_depth_scores(3)
    assert train_none == 1.0  # 無限制樹完美記憶訓練資料
    assert train_none > train_3  # 比限制深度的 train 高(過擬合)


# ===== ch02 集成 =====
def test_ensemble_beats_single_tree() -> None:
    result = compare_ensembles()
    assert result["forest"] > result["tree"]  # 森林勝單棵樹
    assert result["boosting"] > result["tree"]


# ===== ch03 聚類 =====
def test_inertia_decreases_with_k() -> None:
    assert kmeans_inertia(1) > kmeans_inertia(3)  # k 越大 inertia 越小


def test_silhouette_finds_true_k() -> None:
    assert best_k_by_silhouette(range(2, 6)) == 3  # 資料真實 3 群


# ===== ch04 PCA =====
def test_pca_retains_information() -> None:
    # 6 維降到 3 維應保留大部分變異
    assert pca_explained_variance(3) > 0.6
    assert pca_explained_variance(6) == 1.0  # 全部維度保留 100%


def test_pca_auto_dims() -> None:
    dims = pca_dims_for_variance(0.95)
    assert 1 <= dims <= 6  # 保留 95% 變異所需維度


# ===== ch05 調參 =====
def test_grid_search() -> None:
    params, cv_f1 = grid_search_rf()
    assert "n_estimators" in params
    assert "max_depth" in params
    assert cv_f1 > 0.8


def test_random_search_comparable() -> None:
    assert random_search_rf() > 0.8  # 少量嘗試也達到好結果


# ===== ch06 不平衡 =====
def test_class_weight_improves_recall() -> None:
    recall_none = imbalance_recall(use_class_weight=False)
    recall_balanced = imbalance_recall(use_class_weight=True)
    assert recall_balanced > recall_none  # class_weight 大幅提升 recall
    assert recall_none < 0.2  # 無處理時 recall 極低
    assert recall_balanced > 0.5  # 加權後大幅改善


# ===== ch07 可解釋性 =====
def test_permutation_identifies_informative() -> None:
    # 資料只有前 3 個特徵有用,permutation 應把它們排前面
    top3 = permutation_top_features(3)
    assert set(top3) <= {0, 1, 2}  # 最重要的 3 個都在前 3 個特徵中


# ===== ch08 端到端 =====
def test_advanced_pipeline() -> None:
    result = advanced_pipeline()
    assert result["forest_cv_f1"] > 0.7
    assert result["test_f1"] > 0.7
