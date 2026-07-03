# Part 30：生產級 AI 與 LLMOps Production AI & LLMOps

> [Part 28](../28-llm-genai/README.md) 教你用 LLM、[Part 29](../29-ai-applications/README.md) 教你組裝成產品——這一 Part 教你把它**穩定、安全、划算地跑上生產**。LLM 應用有一整套與傳統軟體不同的生產難題:不確定性、成本失控、prompt injection、品質回歸、模型版本漂移。這就是 **LLMOps**。

> 🧭 屬「**資料 / AI 學習線**」,是 **AI Engineer** 學習線(Part 28–30)的收尾。範例用 mock LLM + 純標準庫,CI 不需金鑰。前置:[Part 28](../28-llm-genai/README.md)、[Part 29](../29-ai-applications/README.md);並大量呼應 [Part 14 Web](../14-web/README.md)、[Part 19 雲原生](../19-cloud-native/README.md)、[Part 20 安全](../20-security-system-design/README.md)。

## 章節

| 章 | 標題 |
|----|------|
| 01 | [從 PoC 到生產:LLMOps 概論](01-llmops-intro.md) |
| 02 | [把 LLM 應用 API 化(FastAPI + 串流)](02-serving-llm-apps.md) |
| 03 | [可靠性:重試、逾時、fallback、限流](03-reliability.md) |
| 04 | [可觀測性:logging、tracing、成本與延遲監控](04-observability.md) |
| 05 | [Prompt injection 與 OWASP LLM Top 10](05-prompt-injection-security.md) |
| 06 | [護欄:輸入輸出驗證、PII、內容安全](06-guardrails.md) |
| 07 | [評估回歸與 CI/CD](07-eval-in-cicd.md) |
| 08 | [A/B 測試、金絲雀與版本管理](08-ab-testing-versioning.md) |
| 09 | [資料飛輪與持續改進](09-data-flywheel.md) |
| 10 | [🏗️ Capstone:生產級 LLM 服務](10-capstone-llm-service.md) |

---

⬅️ 上一 Part：[AI 應用工程 RAG 與 Agents](../29-ai-applications/README.md)

[⬆️ 回章節總覽](../README.md)
