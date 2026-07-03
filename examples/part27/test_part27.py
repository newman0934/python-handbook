"""Part 27 範例測試:神經元 / 梯度下降 / 手刻 NN / autograd / 卷積 /
注意力 / 訓練技巧 / 通用網路。"""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from examples.part27.deep_learning import (
    NeuralNet,
    Value,
    attention,
    conv2d,
    dense_layer,
    dropout,
    gradient_descent,
    he_scale,
    lr_schedule,
    max_pool,
    numerical_grad,
    relu,
    should_stop,
    sigmoid,
    softmax,
    train_xor,
)


# ===== ch01 神經元 =====
def test_activations() -> None:
    assert relu(np.array([-1.0, 2.0]))[0] == 0.0
    assert relu(np.array([-1.0, 2.0]))[1] == 2.0
    assert sigmoid(np.array([0.0]))[0] == 0.5


def test_dense_layer() -> None:
    x = np.array([1.0, 2.0])
    w = np.array([[0.5, -0.3], [0.1, 0.8]])
    b = np.array([0.3, 0.0])
    out = dense_layer(x, w, b, relu)
    assert out.shape == (2,)
    assert np.isclose(out[0], 0.2)  # 0.5-0.6+0.3


# ===== ch02 梯度下降 =====
def test_gradient_descent_converges() -> None:
    result = gradient_descent(0.0, lr=0.1, steps=50)
    assert abs(result - 3.0) < 0.1  # 收斂到最小值 3


def test_gradient_descent_diverges_large_lr() -> None:
    result = gradient_descent(0.0, lr=1.1, steps=5)
    assert abs(result - 3.0) > 3  # 學習率太大發散


def test_numerical_grad() -> None:
    grad = numerical_grad(lambda w: (w - 3) ** 2, 1.5)
    assert grad == pytest.approx(-3.0, abs=0.01)  # 2(1.5-3) = -3


# ===== ch03 手刻 NN =====
def test_xor_learned() -> None:
    assert train_xor() == 1.0  # 100% 學會 XOR(單層做不到)


# ===== ch04 autograd =====
def test_autograd() -> None:
    a = Value(2.0)
    b = Value(3.0)
    f = a * b + a
    f.backward()
    assert f.data == 8.0
    assert a.grad == 4.0  # df/da = b+1
    assert b.grad == 2.0  # df/db = a


# ===== ch05 卷積 + 池化 =====
def test_conv2d_detects_edge() -> None:
    image = np.array([[0, 0, 1, 1], [0, 0, 1, 1], [0, 0, 1, 1], [0, 0, 1, 1]], dtype=float)
    kernel = np.array([[1, -1], [1, -1]], dtype=float)
    feat = conv2d(image, kernel)
    assert feat.shape == (3, 3)
    assert feat[0, 1] == -2.0  # 邊緣處強反應
    assert feat[0, 0] == 0.0  # 平坦處無反應


def test_max_pool() -> None:
    x = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]], dtype=float)
    pooled = max_pool(x, size=2)
    assert pooled.shape == (2, 2)
    assert pooled[0, 0] == 6.0  # 左上 2x2 的最大值
    assert pooled[1, 1] == 16.0


# ===== ch06 注意力 =====
def test_attention_weights_sum_to_one() -> None:
    Q = np.array([[1, 0], [0, 1]], dtype=float)
    _, weights = attention(Q, Q, Q)
    assert np.allclose(weights.sum(axis=1), 1.0)  # 每列權重和為 1


def test_attention_similar_tokens() -> None:
    # token0 和 token2 相同 → 互相注意力高
    Q = np.array([[1, 0, 1, 0], [0, 1, 0, 1], [1, 0, 1, 0]], dtype=float)
    V = np.eye(3) * 10
    _, weights = attention(Q, Q, V)
    assert weights[0, 2] > weights[0, 1]  # token0 對 token2 > 對 token1


def test_softmax() -> None:
    result = softmax(np.array([1.0, 2.0, 3.0]))
    assert np.isclose(result.sum(), 1.0)
    assert result[2] > result[0]  # 大的值權重大


# ===== ch07 訓練技巧 =====
def test_dropout_training_vs_inference() -> None:
    rng = np.random.default_rng(0)
    x = np.ones(100)
    train_out = dropout(x, 0.5, training=True, rng=rng)
    assert (train_out == 0).sum() > 0  # 有些被關閉
    infer_out = dropout(x, 0.5, training=False, rng=rng)
    assert np.array_equal(infer_out, x)  # 推論時全保留


def test_he_scale() -> None:
    assert he_scale(100) == pytest.approx(np.sqrt(2 / 100))


def test_lr_schedule() -> None:
    assert lr_schedule(0, 0.1, 10, 100) == 0.0  # warmup 起點
    assert lr_schedule(10, 0.1, 10, 100) == pytest.approx(0.1)  # warmup 頂點
    assert lr_schedule(10, 0.1, 10, 100) > lr_schedule(99, 0.1, 10, 100)  # 之後衰減


def test_early_stopping() -> None:
    assert should_stop([0.5, 0.4, 0.3, 0.31, 0.32, 0.33]) is True  # 不再改善
    assert should_stop([0.5, 0.4, 0.3, 0.25]) is False  # 還在改善


# ===== ch08 通用網路 =====
def test_general_nn_learns_moons() -> None:
    x, y = make_moons(n_samples=500, noise=0.2, random_state=42)
    y = y.reshape(-1, 1)
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.3, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    x_train = scaler.fit_transform(x_train)
    x_test = scaler.transform(x_test)
    net = NeuralNet([2, 16, 8, 1], lr=0.5)
    net.train(x_train, y_train, epochs=200)
    test_acc = float(np.mean(net.predict(x_test) == y_test))
    assert test_acc > 0.9  # 非線性分類,純 numpy 手刻達 >90%
