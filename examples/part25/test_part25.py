"""Part 25 範例測試:學閾值 / split / 特徵工程 / 回歸 / 分類 / 評估 /
過擬合正則化 CV / 端到端 Pipeline。"""

from __future__ import annotations

import numpy as np
import pytest

from examples.part25.ml import (
    classify_with_threshold,
    cv_score,
    end_to_end_pipeline,
    evaluate_classification,
    fit_linear_regression,
    learn_threshold,
    one_hot,
    polynomial_fit,
    sigmoid,
    standardize,
    train_with_proper_split,
)


# ===== ch01 學閾值 =====
def test_learn_threshold() -> None:
    t, acc = learn_threshold([1, 2, 3, 4, 6, 7, 8, 9], [0, 0, 0, 1, 1, 1, 1, 1])
    assert t == 4  # 資料真正分界
    assert acc == 1.0


# ===== ch02 工作流 =====
def test_split_train_ge_test() -> None:
    train_acc, test_acc = train_with_proper_split()
    assert 0.7 < test_acc <= 1.0
    assert train_acc >= test_acc - 0.05  # train 通常略高


# ===== ch03 特徵工程 =====
def test_standardize_zero_mean_unit_std() -> None:
    scaled = standardize(np.array([[10.0], [20.0], [30.0], [40.0]]))
    assert abs(scaled.mean()) < 1e-9
    assert abs(scaled.std() - 1.0) < 1e-6


def test_one_hot_orthogonal() -> None:
    result = one_hot(["a", "b", "a", "c"])
    assert result.shape == (4, 3)  # 3 個類別 → 3 欄
    assert (result.sum(axis=1) == 1).all()  # 每列剛好一個 1


# ===== ch04 線性回歸 =====
def test_linear_regression_recovers_coefficients() -> None:
    coefs, intercept, r2 = fit_linear_regression()
    assert coefs[0] == pytest.approx(50, abs=2)  # 坪數係數 ≈ 50
    assert coefs[1] == pytest.approx(30, abs=5)  # 房間係數 ≈ 30
    assert intercept == pytest.approx(100, abs=20)
    assert r2 > 0.99  # 乾淨合成資料


# ===== ch05 分類 =====
def test_sigmoid() -> None:
    assert sigmoid(0) == 0.5
    assert sigmoid(100) == pytest.approx(1.0)
    assert sigmoid(-100) == pytest.approx(0.0)


def test_threshold_classification() -> None:
    proba = [0.2, 0.4, 0.6, 0.9]
    assert classify_with_threshold(proba, 0.5) == [0, 0, 1, 1]
    assert classify_with_threshold(proba, 0.3) == [0, 1, 1, 1]  # 降閾值 → 更多正類


# ===== ch06 評估指標 =====
def test_precision_recall() -> None:
    # 真:5 個正類;預測抓到 4 個,誤報 2 個
    y_true = [1, 1, 1, 1, 1, 0, 0, 0]
    y_pred = [1, 1, 1, 1, 0, 1, 1, 0]
    m = evaluate_classification(y_true, y_pred)
    assert m["recall"] == 0.8  # 5 個真正類抓 4 個
    assert m["precision"] == pytest.approx(0.667, abs=0.01)  # 判 6 個正類中 4 對


# ===== ch07 過擬合 / 正則化 / CV =====
def test_overfitting_high_degree() -> None:
    tr_low, te_low = polynomial_fit(degree=15)  # 過擬合
    tr_good, te_good = polynomial_fit(degree=3)  # 剛好
    assert tr_low > 0.99  # 訓練幾乎完美
    assert te_low < te_good  # 但測試遠差於恰當次數(過擬合)


def test_regularization_fixes_overfitting() -> None:
    _, te_none = polynomial_fit(degree=15, alpha=0.0)
    _, te_reg = polynomial_fit(degree=15, alpha=0.001)
    assert te_reg > te_none  # 正則化改善過擬合


def test_cross_validation() -> None:
    mean, std = cv_score(degree=3)
    assert mean > 0.8  # 恰當次數 CV 表現好
    assert std >= 0


# ===== ch08 端到端 =====
def test_end_to_end_pipeline() -> None:
    result = end_to_end_pipeline()
    assert result["best_C"] in (0.01, 0.1, 1, 10)
    assert result["test_auc"] > 0.8  # 良好的區分力
