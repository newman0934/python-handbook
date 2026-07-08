# Part 28：LLM 與生成式 AI 基礎 LLM & Generative AI Foundations

> 用 LLM 建應用的地基：LLM 原理、呼叫 Claude API、prompt engineering、結構化輸出與 tool use、串流、embeddings 與向量檢索、成本優化、評估。

> 🧭 本 Part 屬於「**資料 / AI / 部署主線**」(Part 23–31),對應 **AI Engineer / AI Application Engineer** 職位。範例以 Anthropic **Claude API**(`claude-opus-4-8`)為主;可執行範例用 mock client,CI 不需金鑰。

## 章節

| 章 | 標題 |
|----|------|
| 01 | [LLM 原理:token、context、取樣](01-llm-fundamentals.md) |
| 02 | [呼叫 LLM API(Anthropic Claude SDK)](02-calling-llm-api.md) |
| 03 | [Prompt engineering](03-prompt-engineering.md) |
| 04 | [結構化輸出與 function calling / tool use](04-structured-output-tools.md) |
| 05 | [串流與非同步回應](05-streaming-async.md) |
| 06 | [Embeddings 與語意搜尋](06-embeddings-semantic-search.md) |
| 07 | [向量資料庫 (pgvector / Chroma / FAISS)](07-vector-databases.md) |
| 08 | [成本、延遲、快取與限流](08-cost-latency-caching.md) |
| 09 | [LLM 應用評估與 prompt 測試](09-evaluation.md) |

---

## 📌 模型與定價參考表（最後校正：2026-07-08）

> ⚠️ **模型 ID、價格、context 長度會隨官方更新而變動。** 本表集中列出，供 Part 28–30 各章引用；
> 各章行文盡量避免散落硬編的價格數字。使用前請以官方最新資訊為準：
> [Anthropic — Models overview](https://docs.anthropic.com/en/docs/about-claude/models)。

| 模型 | Model ID | Context | 輸入 $/1M | 輸出 $/1M | 定位 |
|------|----------|---------|-----------|-----------|------|
| Claude Opus 4.8 | `claude-opus-4-8` | 1M | $5 | $25 | **本書預設**，難任務、推理 |
| Claude Sonnet 5 | `claude-sonnet-5` | 1M | $3 | $15 | 平衡型，日常主力 |
| Claude Haiku 4.5 | `claude-haiku-4-5` | 200K | $1 | $5 | 便宜快速，分類/抽取等輕任務 |
| Claude Fable 5 | `claude-fable-5` | 1M | $10 | $50 | 最強、最貴，最艱難的推理/長流程 |

**選型口訣**(呼應 [ch08 成本](08-cost-latency-caching.md)):簡單任務用 Haiku、日常用 Sonnet、難題才上 Opus/Fable——同任務常可省數倍。

---

[⬆️ 回章節總覽](../README.md)
