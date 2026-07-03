"""Part 27 深度學習範例:神經元/前向傳播 / 梯度下降 / 手刻 NN(XOR) /
mini autograd / 卷積池化 / 注意力 / 訓練技巧 / 通用網路。

純 numpy 手刻(不需框架/GPU);固定 seed 確保可重現。
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


# ===== ch01 神經元與激活 =====
def relu(z: np.ndarray) -> np.ndarray:
    return np.asarray(np.maximum(0, z))


def sigmoid(z: np.ndarray) -> np.ndarray:
    return np.asarray(1 / (1 + np.exp(-np.clip(z, -500, 500))))


def dense_layer(x: np.ndarray, w: np.ndarray, b: np.ndarray, activation: Callable) -> np.ndarray:  # type: ignore[type-arg]
    return np.asarray(activation(w @ x + b))


# ===== ch02 梯度下降 =====
def gradient_descent(w: float, lr: float, steps: int) -> float:
    """最小化 (w-3)^2,梯度 2(w-3)。"""
    for _ in range(steps):
        w = w - lr * 2 * (w - 3)
    return w


def numerical_grad(f: Callable[[float], float], w: float, eps: float = 1e-5) -> float:
    return (f(w + eps) - f(w - eps)) / (2 * eps)


# ===== ch03 手刻 NN 學 XOR =====
def sigmoid_deriv(a: np.ndarray) -> np.ndarray:
    return np.asarray(a * (1 - a))


def train_xor(epochs: int = 3000, lr: float = 0.5) -> float:
    """訓練 2-4-1 網路學 XOR,回最終準確率。"""
    x = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=float)
    y = np.array([[0], [1], [1], [0]], dtype=float)
    rng = np.random.default_rng(42)
    w1 = rng.normal(0, 1, (2, 4))
    b1 = np.zeros((1, 4))
    w2 = rng.normal(0, 1, (4, 1))
    b2 = np.zeros((1, 1))
    for _ in range(epochs):
        h = sigmoid(x @ w1 + b1)
        out = sigmoid(h @ w2 + b2)
        d_out = (out - y) * sigmoid_deriv(out)
        d_h = (d_out @ w2.T) * sigmoid_deriv(h)
        w2 -= lr * (h.T @ d_out)
        b2 -= lr * d_out.sum(axis=0, keepdims=True)
        w1 -= lr * (x.T @ d_h)
        b1 -= lr * d_h.sum(axis=0, keepdims=True)
    out = sigmoid(sigmoid(x @ w1 + b1) @ w2 + b2)
    return float(np.mean((out > 0.5).astype(int) == y))


# ===== ch04 mini autograd =====
class Value:
    def __init__(self, data: float, children: tuple[Value, ...] = ()) -> None:
        self.data = data
        self.grad = 0.0
        self._backward: Callable[[], None] = lambda: None
        self._prev = set(children)

    def __add__(self, other: Value | float) -> Value:
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other))

        def _backward() -> None:
            self.grad += out.grad
            other.grad += out.grad

        out._backward = _backward
        return out

    def __mul__(self, other: Value | float) -> Value:
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other))

        def _backward() -> None:
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad

        out._backward = _backward
        return out

    def backward(self) -> None:
        topo: list[Value] = []
        visited: set[Value] = set()

        def build(v: Value) -> None:
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build(child)
                topo.append(v)

        build(self)
        self.grad = 1.0
        for v in reversed(topo):
            v._backward()


# ===== ch05 卷積 + 池化 =====
def conv2d(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    ih, iw = image.shape
    kh, kw = kernel.shape
    out = np.zeros((ih - kh + 1, iw - kw + 1))
    for i in range(out.shape[0]):
        for j in range(out.shape[1]):
            out[i, j] = float(np.sum(image[i : i + kh, j : j + kw] * kernel))
    return out


def max_pool(x: np.ndarray, size: int = 2) -> np.ndarray:
    h, w = x.shape
    out = np.zeros((h // size, w // size))
    for i in range(out.shape[0]):
        for j in range(out.shape[1]):
            out[i, j] = float(np.max(x[i * size : (i + 1) * size, j * size : (j + 1) * size]))
    return out


# ===== ch06 注意力 =====
def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    e = np.exp(x - x.max(axis=axis, keepdims=True))
    return np.asarray(e / e.sum(axis=axis, keepdims=True))


def attention(Q: np.ndarray, K: np.ndarray, V: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    d_k = Q.shape[-1]
    scores = Q @ K.T / np.sqrt(d_k)
    weights = softmax(scores)
    return weights @ V, weights


# ===== ch07 訓練技巧 =====
def dropout(x: np.ndarray, rate: float, training: bool, rng: np.random.Generator) -> np.ndarray:
    if not training or rate == 0:
        return x
    mask = (rng.random(x.shape) >= rate) / (1 - rate)
    return np.asarray(x * mask)


def he_scale(fan_in: int) -> float:
    return float(np.sqrt(2 / fan_in))


def lr_schedule(step: int, base_lr: float, warmup: int, total: int) -> float:
    if step < warmup:
        return base_lr * step / warmup
    return base_lr * (1 - (step - warmup) / (total - warmup))


def should_stop(val_losses: list[float], patience: int = 3) -> bool:
    if len(val_losses) <= patience:
        return False
    return min(val_losses[-patience:]) >= min(val_losses[:-patience])


# ===== ch08 通用網路 =====
def relu_deriv(z: np.ndarray) -> np.ndarray:
    return (z > 0).astype(float)


class NeuralNet:
    def __init__(self, sizes: list[int], lr: float = 0.5, seed: int = 42) -> None:
        rng = np.random.default_rng(seed)
        self.lr = lr
        self.weights = [
            rng.normal(0, np.sqrt(2 / sizes[i]), (sizes[i], sizes[i + 1]))
            for i in range(len(sizes) - 1)
        ]
        self.biases = [np.zeros((1, sizes[i + 1])) for i in range(len(sizes) - 1)]

    def forward(self, x: np.ndarray) -> np.ndarray:
        self.zs: list[np.ndarray] = []
        self.activations = [x]
        h = x
        for i in range(len(self.weights) - 1):
            z = h @ self.weights[i] + self.biases[i]
            self.zs.append(z)
            h = relu(z)
            self.activations.append(h)
        z = h @ self.weights[-1] + self.biases[-1]
        self.zs.append(z)
        out = sigmoid(z)
        self.activations.append(out)
        return out

    def backward(self, y: np.ndarray) -> None:
        m = y.shape[0]
        d = (self.activations[-1] - y) / m
        for i in reversed(range(len(self.weights))):
            d_w = self.activations[i].T @ d
            d_b = d.sum(axis=0, keepdims=True)
            if i > 0:
                d = (d @ self.weights[i].T) * relu_deriv(self.zs[i - 1])
            self.weights[i] -= self.lr * d_w
            self.biases[i] -= self.lr * d_b

    def train(self, x: np.ndarray, y: np.ndarray, epochs: int, batch: int = 32) -> None:
        rng = np.random.default_rng(0)
        for _ in range(epochs):
            idx = rng.permutation(len(x))
            for s in range(0, len(x), batch):
                bi = idx[s : s + batch]
                self.forward(x[bi])
                self.backward(y[bi])

    def predict(self, x: np.ndarray) -> np.ndarray:
        return (self.forward(x) > 0.5).astype(int)
