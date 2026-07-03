"""Part 29 範例測試:RAG / chunking / 混合檢索 / 評估 / agent / MCP /
記憶 / 多 agent / chain / 端到端 Capstone。"""

from __future__ import annotations

import pytest

from examples.part29.rag_agents import (
    ConversationMemory,
    KnowledgeBase,
    MCPServer,
    Orchestrator,
    Step,
    Task,
    ToolSpec,
    bm25_lite,
    chain,
    chunk_fixed,
    faithfulness,
    mrr,
    rag_answer,
    rank,
    recall_at_k,
    reciprocal_rank_fusion,
    run_react,
)


# ===== ch02 chunking =====
def test_chunk_fixed_overlap() -> None:
    chunks = chunk_fixed("abcdefghijklmnopqrstuvwxyz", size=10, overlap=3)
    assert chunks[0] == "abcdefghij"
    assert chunks[1] == "hijklmnopq"  # 步長 7,與前片重疊 "hij"
    assert chunks[0][-3:] == chunks[1][:3]


def test_chunk_overlap_validation() -> None:
    with pytest.raises(ValueError, match="overlap"):
        chunk_fixed("abc", size=5, overlap=5)


# ===== ch03 混合檢索 =====
def test_bm25_matches_keyword() -> None:
    docs = {"d1": "python asyncio 並發", "d2": "貓 動物"}
    scores = bm25_lite("asyncio", docs)
    assert scores["d1"] > scores["d2"]


def test_rrf_fuses_rankings() -> None:
    # 兩路都把 d1 排第一 → d1 融合分最高
    fused = reciprocal_rank_fusion([["d1", "d2", "d3"], ["d1", "d3", "d2"]])
    assert fused[0] == "d1"


def test_rrf_rewards_agreement() -> None:
    # d2 在兩路都排前面,d3 只在一路 → d2 應在 d3 之前
    fused = reciprocal_rank_fusion([["d1", "d2", "d3"], ["d2", "d1", "d3"]])
    assert fused.index("d2") < fused.index("d3")


# ===== ch04 RAG 評估 =====
@pytest.mark.parametrize(
    ("retrieved", "relevant", "k", "expected"),
    [
        (["d1", "d2", "d3"], ["d1"], 3, 1.0),
        (["d2", "d3", "d1"], ["d1", "d4"], 3, 0.5),
        (["d2", "d3"], ["d1"], 2, 0.0),
    ],
)
def test_recall_at_k(retrieved: list[str], relevant: list[str], k: int, expected: float) -> None:
    assert recall_at_k(retrieved, relevant, k) == expected


def test_mrr_first_relevant_rank() -> None:
    assert mrr(["d3", "d1", "d5"], ["d1"]) == 0.5  # 相關的排第 2
    assert mrr(["d1", "d2"], ["d1"]) == 1.0
    assert mrr(["d3", "d4"], ["d1"]) == 0.0


def test_faithfulness_detects_hallucination() -> None:
    ctx = "python 由 guido 於 1991 發布"
    assert faithfulness(["guido", "1991"], ctx) == 1.0  # 全支持
    assert faithfulness(["guido", "2050"], ctx) == 0.5  # 2050 是幻覺


# ===== ch05 ReAct agent =====
def test_react_multi_step() -> None:
    tools = {
        "lookup": lambda x: "250萬(2500000)",
        "calc": lambda x: str(eval(x, {"__builtins__": {}}, {})),  # noqa: S307
    }

    def policy(question: str, history: list[Step]) -> Step:
        n = len(history)
        if n == 0:
            return Step("先查", "lookup", "台北人口")
        if n == 1:
            return Step("再算", "calc", "2500000*2")
        return Step("完成", None, None)

    history = run_react(policy, tools, "台北人口兩倍")
    assert len(history) == 2
    assert history[0].action == "lookup"
    assert history[1].observation == "5000000"


def test_react_respects_max_steps() -> None:
    tools = {"noop": lambda x: "again"}
    # 永不宣告完成的 policy → 應被 max_steps 攔住
    policy = lambda q, h: Step("loop", "noop", "x")  # noqa: E731
    history = run_react(policy, tools, "q", max_steps=3)
    assert len(history) == 3


# ===== ch06 MCP =====
def test_mcp_list_and_call() -> None:
    server = MCPServer("weather")
    server.register(
        ToolSpec("get_temp", "查氣溫", {"type": "object"}),
        lambda city: f"{city} 25 度",
    )
    assert [t.name for t in server.list_tools()] == ["get_temp"]
    result = server.call_tool("get_temp", {"city": "Taipei"})
    assert result == {"isError": False, "content": "Taipei 25 度"}


def test_mcp_unknown_tool_errors() -> None:
    server = MCPServer("s")
    result = server.call_tool("nope", {})
    assert result["isError"] is True


# ===== ch07 對話記憶 =====
def test_memory_respects_budget() -> None:
    mem = ConversationMemory(budget=60, system="你是助理")
    for i in range(6):
        mem.add("user", f"問題{i}")
        mem.add("assistant", f"這是問題{i}的回覆")
    summary, kept, used = mem.build_context()
    assert used <= mem.budget
    assert len(kept) < len(mem.messages)  # 有訊息被壓縮
    assert "摘要" in summary


def test_memory_no_overflow_no_summary() -> None:
    mem = ConversationMemory(budget=200, system="s")
    mem.add("user", "hi")
    summary, kept, _ = mem.build_context()
    assert summary == ""
    assert len(kept) == 1


# ===== ch08 多 agent =====
def test_orchestrator_routes() -> None:
    orch = Orchestrator()
    orch.register("research", lambda p: f"查到 {p}")
    orch.register("code", lambda p: f"寫好 {p}")
    results = orch.run_plan([Task("research", "asyncio"), Task("code", "下載器")])
    assert results[0].output == "查到 asyncio"
    assert results[1].output == "寫好 下載器"


def test_orchestrator_graceful_degrade() -> None:
    orch = Orchestrator()
    result = orch.dispatch(Task("deploy", "x"))
    assert result.worker == "orchestrator"
    assert "無法處理" in result.output


# ===== ch09 mini chain =====
def test_chain_pipes_steps() -> None:
    pipeline = chain() | (lambda s: {**s, "b": s["a"] + "1"}) | (lambda s: {**s, "c": s["b"] + "2"})
    out = pipeline.invoke({"a": "x"})
    assert out["c"] == "x12"


# ===== ch10 Capstone 端到端 =====
def test_capstone_retrieves_correct_source() -> None:
    kb = KnowledgeBase()
    kb.index("d1", "asyncio 事件迴圈並發。GIL 限制執行緒。", "concurrency.md")
    kb.index("d2", "RAG 用向量檢索,embedding 是關鍵。", "rag.md")

    _, sources = rag_answer(kb, "rag 檢索")
    assert "rag.md" in sources

    _, sources2 = rag_answer(kb, "gil 執行緒")
    assert "concurrency.md" in sources2


def test_capstone_source_hit_rate() -> None:
    kb = KnowledgeBase()
    kb.index("d1", "asyncio 事件迴圈並發。GIL 限制執行緒。", "concurrency.md")
    kb.index("d2", "RAG 用向量檢索,embedding 是關鍵。", "rag.md")
    cases = [
        ("gil 執行緒", "concurrency.md"),
        ("rag 檢索", "rag.md"),
    ]
    hits = sum(1 for q, src in cases if src in rag_answer(kb, q)[1])
    assert hits / len(cases) == 1.0


def test_rank_orders_descending() -> None:
    assert rank({"a": 1.0, "b": 3.0, "c": 2.0}) == ["b", "c", "a"]
