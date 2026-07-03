"""Part 28 LLM 與生成式 AI 基礎範例:取樣 / mock Claude client / prompt /
tool use / 串流 / embeddings / 向量索引 / 成本 / 評估。

LLM 呼叫用 mock client(不需金鑰);向量相似度用 numpy。
"""

from __future__ import annotations

import math
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field

import numpy as np


# ===== ch01 取樣:temperature softmax =====
def softmax_with_temperature(logits: list[float], temperature: float) -> list[float]:
    if temperature <= 0:
        best = max(range(len(logits)), key=lambda i: logits[i])
        return [1.0 if i == best else 0.0 for i in range(len(logits))]
    scaled = [z / temperature for z in logits]
    mx = max(scaled)
    exps = [math.exp(z - mx) for z in scaled]
    total = sum(exps)
    return [e / total for e in exps]


# ===== ch02 mock Claude client + 多輪對話 =====
@dataclass
class TextBlock:
    type: str
    text: str


@dataclass
class Message:
    content: list[TextBlock]
    stop_reason: str
    model: str


class MockAnthropic:
    """模擬 anthropic.Anthropic().messages.create(教學/測試用)。"""

    def __init__(self, canned: dict[str, str] | None = None) -> None:
        self.canned = canned or {}
        self.call_count = 0

    def create(
        self,
        model: str,
        max_tokens: int,
        messages: list[dict[str, str]],
        system: str | None = None,
    ) -> Message:
        self.call_count += 1
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        reply = self.canned.get(last_user, f"(mock: {last_user})")
        return Message([TextBlock("text", reply)], "end_turn", model)


class Conversation:
    def __init__(self, client: MockAnthropic, model: str, system: str | None = None) -> None:
        self.client = client
        self.model = model
        self.system = system
        self.messages: list[dict[str, str]] = []

    def send(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        resp = self.client.create(
            model=self.model, max_tokens=1024, system=self.system, messages=self.messages
        )
        reply = next(b.text for b in resp.content if b.type == "text")
        self.messages.append({"role": "assistant", "content": reply})
        return reply


# ===== ch03 prompt 組裝 =====
def build_few_shot(task: str, examples: list[tuple[str, str]], query: str) -> str:
    parts = [task, "", "範例:"]
    parts.extend(f"輸入: {inp} → {out}" for inp, out in examples)
    parts.append(f"\n輸入: {query} →")
    return "\n".join(parts)


# ===== ch04 tool use =====
@dataclass
class ToolCall:
    name: str
    args: dict[str, object]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., str]] = {}

    def register(self, name: str, func: Callable[..., str]) -> None:
        self._tools[name] = func

    def execute(self, call: ToolCall) -> str:
        if call.name not in self._tools:
            return f"錯誤:未知工具 {call.name}"
        return self._tools[call.name](**call.args)


# ===== ch05 串流(asyncio)=====
async def stream_tokens(reply: str) -> AsyncIterator[str]:
    for chunk in reply.split():
        yield chunk + " "


async def collect_stream(reply: str) -> str:
    parts = [chunk async for chunk in stream_tokens(reply)]
    return "".join(parts).strip()


# ===== ch06 餘弦相似度 + 語意搜尋 =====
def cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.asarray(a, dtype=np.float64)
    vb = np.asarray(b, dtype=np.float64)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))


def semantic_search(
    query: list[float], docs: dict[str, list[float]], top_k: int = 3
) -> list[tuple[float, str]]:
    scored = [(cosine_similarity(query, vec), text) for text, vec in docs.items()]
    scored.sort(reverse=True)
    return scored[:top_k]


# ===== ch07 向量索引 =====
@dataclass
class VectorIndex:
    _ids: list[str] = field(default_factory=list)
    _vectors: list[np.ndarray] = field(default_factory=list)
    _metadata: list[dict[str, str]] = field(default_factory=list)

    @staticmethod
    def _normalize(vec: list[float]) -> np.ndarray:
        v = np.asarray(vec, dtype=np.float64)
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else v

    def add(self, doc_id: str, vector: list[float], metadata: dict[str, str]) -> None:
        self._ids.append(doc_id)
        self._vectors.append(self._normalize(vector))
        self._metadata.append(metadata)

    def search(
        self, query: list[float], k: int = 3, category: str | None = None
    ) -> list[tuple[float, str]]:
        q = self._normalize(query)
        results: list[tuple[float, str]] = []
        for doc_id, vec, meta in zip(self._ids, self._vectors, self._metadata, strict=True):
            if category is not None and meta.get("category") != category:
                continue
            results.append((float(np.dot(q, vec)), doc_id))
        results.sort(reverse=True, key=lambda r: r[0])
        return results[:k]


# ===== ch08 成本計算 + 分流 =====
PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-8": {"input": 5.0, "output": 25.0},
    "claude-sonnet-5": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5": {"input": 1.0, "output": 5.0},
}


def cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING[model]
    return input_tokens / 1e6 * p["input"] + output_tokens / 1e6 * p["output"]


def route(task_kind: str) -> str:
    return "claude-haiku-4-5" if task_kind == "simple" else "claude-opus-4-8"


# ===== ch09 評估 =====
def rule_scorer(expected: str, output: str) -> bool:
    return output.strip().lower() == expected.strip().lower()


def run_eval(cases: list[dict[str, str]], app: dict[str, str]) -> float:
    """回通過率:expected 用精確匹配、must_contain 用關鍵字。"""
    passed = 0
    for case in cases:
        output = app.get(case["input"], "")
        if "expected" in case:
            ok = rule_scorer(case["expected"], output)
        else:
            ok = case["must_contain"] in output
        passed += ok
    return passed / len(cases)
