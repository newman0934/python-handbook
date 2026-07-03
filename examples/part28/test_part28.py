"""Part 28 範例的驗證測試。

執行：pytest examples/part28
"""

from __future__ import annotations

import asyncio

import pytest

from examples.part28.llm import (
    Conversation,
    MockAnthropic,
    ToolCall,
    ToolRegistry,
    VectorIndex,
    build_few_shot,
    collect_stream,
    cosine_similarity,
    cost,
    route,
    run_eval,
    semantic_search,
    softmax_with_temperature,
)


# --- ch01 取樣 ---
def test_softmax_sums_to_one() -> None:
    probs = softmax_with_temperature([2.0, 1.0, 0.5], 1.0)
    assert abs(sum(probs) - 1.0) < 1e-9
    assert probs[0] > probs[1] > probs[2]  # logit 高→機率高


def test_low_temperature_approaches_greedy() -> None:
    probs = softmax_with_temperature([2.0, 1.0, 0.5], 0.01)
    assert probs[0] > 0.99  # 低溫趨近貪婪
    # temperature=0 就是貪婪
    assert softmax_with_temperature([2.0, 1.0, 0.5], 0.0) == [1.0, 0.0, 0.0]


def test_high_temperature_flattens() -> None:
    low = softmax_with_temperature([2.0, 1.0, 0.5], 0.5)
    high = softmax_with_temperature([2.0, 1.0, 0.5], 5.0)
    assert high[0] < low[0]  # 高溫分布更平,最大值機率下降


# --- ch02 mock client + 多輪 ---
def test_conversation_stateless_history() -> None:
    client = MockAnthropic(canned={"我叫 Alice": "hi Alice", "名字?": "Alice"})
    conv = Conversation(client, model="claude-opus-4-8")
    assert conv.send("我叫 Alice") == "hi Alice"
    assert conv.send("名字?") == "Alice"
    assert len(conv.messages) == 4  # 2 user + 2 assistant
    assert client.call_count == 2


# --- ch03 prompt ---
def test_build_few_shot() -> None:
    prompt = build_few_shot("分類", [("好", "pos"), ("爛", "neg")], "普通")
    assert "輸入: 好 → pos" in prompt
    assert prompt.rstrip().endswith("輸入: 普通 →")


# --- ch04 tool use ---
def test_tool_registry() -> None:
    reg = ToolRegistry()
    reg.register("get_weather", lambda city: f"{city} 晴天")
    assert reg.execute(ToolCall("get_weather", {"city": "台北"})) == "台北 晴天"
    # 未註冊工具被擋(安全)
    assert "未知工具" in reg.execute(ToolCall("delete_all", {}))


# --- ch05 串流 ---
def test_streaming_collects_all_chunks() -> None:
    result = asyncio.run(collect_stream("Hello streaming world"))
    assert result == "Hello streaming world"


def test_concurrent_streams() -> None:
    async def run() -> list[str]:
        return list(await asyncio.gather(collect_stream("答案 A"), collect_stream("答案 B")))

    assert asyncio.run(run()) == ["答案 A", "答案 B"]


# --- ch06 餘弦相似度 + 語意搜尋 ---
def test_cosine_similarity() -> None:
    assert cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0, 0], [0, 1, 0]) == pytest.approx(0.0)


def test_semantic_search_ranks_by_meaning() -> None:
    docs = {
        "Python 是程式語言": [0.90, 0.10, 0.05],
        "貓是動物": [0.05, 0.10, 0.90],
        "Java 也是程式語言": [0.70, 0.30, 0.10],
    }
    results = semantic_search([0.88, 0.12, 0.05], docs, top_k=2)
    # 程式語言的兩篇排前面,貓被排除
    assert results[0][1] == "Python 是程式語言"
    assert results[1][1] == "Java 也是程式語言"


# --- ch07 向量索引 ---
def test_vector_index_search_and_filter() -> None:
    index = VectorIndex()
    index.add("d1", [0.9, 0.1, 0.05], {"category": "程式"})
    index.add("d2", [0.05, 0.1, 0.9], {"category": "動物"})
    index.add("d3", [0.7, 0.3, 0.1], {"category": "程式"})
    top = index.search([0.88, 0.12, 0.05], k=2)
    assert [doc_id for _, doc_id in top] == ["d1", "d3"]
    # 中繼資料過濾:只在動物類別搜
    filtered = index.search([0.88, 0.12, 0.05], k=3, category="動物")
    assert [doc_id for _, doc_id in filtered] == ["d2"]


# --- ch08 成本 + 分流 ---
def test_cost_calculation() -> None:
    assert cost("claude-opus-4-8", 2000, 500) == pytest.approx(0.0225)
    assert cost("claude-haiku-4-5", 2000, 500) == pytest.approx(0.0045)
    # Opus 比 Haiku 貴 5 倍
    assert cost("claude-opus-4-8", 1000, 1000) == pytest.approx(
        5 * cost("claude-haiku-4-5", 1000, 1000)
    )


def test_routing() -> None:
    assert route("simple") == "claude-haiku-4-5"
    assert route("complex") == "claude-opus-4-8"


# --- ch09 評估 ---
def test_eval_pass_rate_and_regression() -> None:
    cases = [
        {"input": "分類:爛", "expected": "negative"},
        {"input": "台北?", "must_contain": "台灣"},
    ]
    good = {"分類:爛": "negative", "台北?": "台北在台灣"}
    assert run_eval(cases, good) == 1.0
    # 改壞 → 通過率下降(eval 抓到迴歸)
    broken = {"分類:爛": "positive", "台北?": "台北在台灣"}
    assert run_eval(cases, broken) == 0.5
