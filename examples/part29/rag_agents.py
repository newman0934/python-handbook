"""Part 29 AI 應用工程範例:RAG 全流程 / chunking / 混合檢索 / RAG 評估 /
ReAct agent / MCP / 對話記憶 / 多 agent / mini chain / 端到端 Capstone。

LLM 與 embedding 皆用 mock(不需金鑰);向量運算用 numpy。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np


# ===== ch02 chunking =====
def chunk_fixed(text: str, size: int, overlap: int) -> list[str]:
    """固定大小 + overlap;步長 = size - overlap。"""
    if overlap >= size:
        raise ValueError("overlap 必須小於 size")
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        start += size - overlap
    return chunks


# ===== Part28 ch06 / ch01 embedding + 檢索 =====
def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


# ===== ch03 混合檢索 =====
def bm25_lite(query: str, docs: dict[str, str]) -> dict[str, float]:
    import math

    q_terms = query.lower().split()
    n_docs = len(docs)
    df = {t: sum(1 for d in docs.values() if t in d.lower().split()) for t in set(q_terms)}
    scores: dict[str, float] = {}
    for doc_id, text in docs.items():
        toks = text.lower().split()
        scores[doc_id] = sum(
            toks.count(t) * math.log(n_docs / df[t] + 1) for t in q_terms if df.get(t)
        )
    return scores


def rank(scores: dict[str, float]) -> list[str]:
    return sorted(scores, key=lambda d: scores[d], reverse=True)


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[str]:
    fused: dict[str, float] = {}
    for ranking in rankings:
        for position, doc_id in enumerate(ranking):
            fused[doc_id] = fused.get(doc_id, 0.0) + 1 / (k + position + 1)
    return rank(fused)


# ===== ch04 RAG 評估 =====
def recall_at_k(retrieved: list[str], relevant: list[str], k: int) -> float:
    top = set(retrieved[:k])
    rel = set(relevant)
    return len(top & rel) / len(rel) if rel else 0.0


def mrr(retrieved: list[str], relevant: list[str]) -> float:
    rel = set(relevant)
    for i, doc in enumerate(retrieved):
        if doc in rel:
            return 1 / (i + 1)
    return 0.0


def faithfulness(claims: list[str], context: str) -> float:
    if not claims:
        return 0.0
    return sum(1 for c in claims if c in context) / len(claims)


# ===== ch05 ReAct agent =====
@dataclass
class Step:
    thought: str
    action: str | None
    action_input: str | None
    observation: str | None = None


def run_react(
    policy: Callable[[str, list[Step]], Step],
    tools: dict[str, Callable[[str], str]],
    question: str,
    max_steps: int = 5,
) -> list[Step]:
    history: list[Step] = []
    for _ in range(max_steps):
        step = policy(question, history)
        if step.action is None:
            return history
        obs = tools[step.action](step.action_input or "")
        history.append(Step(step.thought, step.action, step.action_input, obs))
    return history


# ===== ch06 MCP =====
@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, object]


class MCPServer:
    def __init__(self, name: str) -> None:
        self.name = name
        self._tools: dict[str, tuple[ToolSpec, Callable[..., str]]] = {}

    def register(self, spec: ToolSpec, func: Callable[..., str]) -> None:
        self._tools[spec.name] = (spec, func)

    def list_tools(self) -> list[ToolSpec]:
        return [spec for spec, _ in self._tools.values()]

    def call_tool(self, name: str, arguments: dict[str, object]) -> dict[str, object]:
        if name not in self._tools:
            return {"isError": True, "content": f"unknown tool {name}"}
        _, func = self._tools[name]
        return {"isError": False, "content": func(**arguments)}


# ===== ch07 對話記憶 =====
@dataclass
class Msg:
    role: str
    content: str


@dataclass
class ConversationMemory:
    budget: int
    system: str = ""
    summary_reserve: int = 20
    messages: list[Msg] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append(Msg(role, content))

    def build_context(self) -> tuple[str, list[Msg], int]:
        avail = self.budget - len(self.system) - self.summary_reserve
        kept: list[Msg] = []
        running = 0
        for m in reversed(self.messages):
            c = len(m.content)
            if running + c > avail:
                break
            kept.insert(0, m)
            running += c
        overflow = self.messages[: len(self.messages) - len(kept)]
        summary = f"[摘要] 先前 {len(overflow)} 則已省略" if overflow else ""
        used = len(self.system) + len(summary) + running
        return summary, kept, used


# ===== ch08 多 agent =====
@dataclass
class Task:
    kind: str
    payload: str


@dataclass
class Result:
    worker: str
    output: str


class Orchestrator:
    def __init__(self) -> None:
        self.routes: dict[str, Callable[[str], str]] = {}

    def register(self, kind: str, handler: Callable[[str], str]) -> None:
        self.routes[kind] = handler

    def dispatch(self, task: Task) -> Result:
        handler = self.routes.get(task.kind)
        if handler is None:
            return Result("orchestrator", f"無法處理 {task.kind}")
        return Result(task.kind, handler(task.payload))

    def run_plan(self, tasks: list[Task]) -> list[Result]:
        return [self.dispatch(t) for t in tasks]


# ===== ch09 mini chain =====
State = dict[str, str]


@dataclass
class Chain:
    steps: list[Callable[[State], State]]

    def __or__(self, step: Callable[[State], State]) -> Chain:
        return Chain(self.steps + [step])

    def invoke(self, state: State) -> State:
        for step in self.steps:
            state = step(state)
        return state


def chain() -> Chain:
    return Chain([])


# ===== ch10 Capstone 端到端 RAG =====
VOCAB = ["asyncio", "gil", "並發", "執行緒", "向量", "embedding", "檢索", "rag"]


def kb_embed(text: str) -> np.ndarray:
    t = text.lower()
    return np.array([1.0 if w in t else 0.0 for w in VOCAB])


@dataclass
class Doc:
    id: str
    text: str
    vec: np.ndarray
    source: str


@dataclass
class KnowledgeBase:
    docs: list[Doc] = field(default_factory=list)

    def index(self, doc_id: str, text: str, source: str, size: int = 30, overlap: int = 5) -> None:
        for i, c in enumerate(chunk_fixed(text, size, overlap)):
            self.docs.append(Doc(f"{doc_id}#{i}", c, kb_embed(c), source))

    def _vec_rank(self, query: str) -> list[str]:
        qv = kb_embed(query)
        return [d.id for d in sorted(self.docs, key=lambda d: cosine(qv, d.vec), reverse=True)]

    def _kw_rank(self, query: str) -> list[str]:
        terms = query.lower().split()
        return [
            d.id
            for d in sorted(
                self.docs, key=lambda d: sum(d.text.lower().count(t) for t in terms), reverse=True
            )
        ]

    def retrieve(self, query: str, k: int = 2) -> list[Doc]:
        fused = reciprocal_rank_fusion([self._vec_rank(query), self._kw_rank(query)])[:k]
        by_id = {d.id: d for d in self.docs}
        return [by_id[t] for t in fused]


def rag_answer(kb: KnowledgeBase, query: str, k: int = 2) -> tuple[str, list[str]]:
    contexts = kb.retrieve(query, k)
    if not contexts:
        return "找不到相關資訊。", []
    return contexts[0].text.strip(), [c.source for c in contexts]
