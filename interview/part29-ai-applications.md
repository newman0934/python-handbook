# Part 29 面試題:AI 應用工程(RAG / Agents)

> 對應 [Part 29 AI 應用工程](../chapters/29-ai-applications/README.md)。**AI Application Engineer 核心**——RAG、chunking、混合檢索、agents、MCP、記憶。

---

## Q1.(必考)RAG 解決什麼?為什麼能減少幻覺?

**考點**:RAG([01-rag-pipeline](../chapters/29-ai-applications/01-rag-pipeline.md))

**答**:RAG(檢索增強生成)解決 LLM 的兩大限制:**知識截止**(不知道私有/最新資料)和**幻覺**。做法:先從你的知識庫**檢索相關事實**,塞進 prompt,讓 LLM **根據檢索到的事實回答**。

**兩階段**:

- **離線**:文件**分塊 → embed → 存向量庫**。
- **線上**:問題 **檢索 top-k → 組裝進 prompt → 生成**。

**為何減少幻覺**:**grounding(接地)**——模型不是從**模糊記憶**挖答案(容易編),而是**根據眼前 context 的事實**回答。再加「資料沒有就說不知道」的**誠實退路**指令。

**追問**:**RAG vs fine-tuning**——RAG 把知識放**外部**(易更新、可溯源、便宜);fine-tune 訓進**權重**(適合風格/技能,但更新貴、不可溯源)。**多數「讓模型知道我的資料」用 RAG**。

---

## Q2. 為什麼要 chunking?chunk size 和 overlap 怎麼取捨?

**考點**:chunking([02-chunking-strategies](../chapters/29-ai-applications/02-chunking-strategies.md))

**答**:為何要分塊:**context 限制**(整份文件塞不下/貴)、**embedding 語意稀釋**(長文的向量太「平均」、誰都不像)、**檢索粒度**(要檢索到剛好回答問題的那小段)。

**取捨**:

- **chunk size**:太大**語意稀釋**、太小**語意破碎**(一句話被切兩半)。
- **overlap**:相鄰片重疊——**防答案落在切割線上被切斷**;**步長 = size − overlap**。常設 size 的 10–20%。

**追問**:策略——固定大小、按句/段/結構、語意、**遞迴切分**(實務預設);要附 **metadata**(來源、頁碼)供溯源與過濾。

---

## Q3. 混合檢索的動機?RRF 融合?

**考點**:混合檢索([03-hybrid-retrieval-rerank](../chapters/29-ai-applications/03-hybrid-retrieval-rerank.md))

**答**:**向量檢索懂語意但對精確字弱**(產品型號、錯誤碼、函式名);**關鍵字(BM25)精確但不懂語意**(同義、換句話說)。**兩者互補** → 混合檢索。

- **稀疏(BM25)**:精確匹配、可解釋。
- **稠密(embedding)**:語意、同義。

**召回 → 精排兩階段**:用**便宜方法(BM25 + 向量)召回一撮**(高 recall)、用**貴模型(cross-encoder rerank)精排**(高 precision)——兼顧品質與成本。

**RRF(倒數排名融合)**:融合兩路結果時**用排名而非分數**(`1/(k+rank)` 累加)——**免調權重、不受量綱影響**(BM25 分和餘弦分量綱不同,不能直接相加)。

**追問**:cross-encoder(把 query+doc 一起編碼,有交互注意力,準但慢,只用於精排小候選集)。

---

## Q4. RAG 為什麼要分層評估?檢索和生成指標?

**考點**:RAG 評估([04-rag-evaluation](../chapters/29-ai-applications/04-rag-evaluation.md))

**答**:RAG 失敗根因分兩種——**檢索錯**(沒撈到答案)vs **生成錯**(撈到了但沒用好/幻覺)。要**分開量測**才能定位該修哪。

- **檢索指標**:**Recall@k**(有沒有撈到,地基)、**Precision@k**(雜訊多不多)、**MRR**(相關的排前面嗎)。
- **生成指標(RAG triad)**:**context 相關、忠實度(抓幻覺,答案有沒有超出 context)、答案相關**。

**eval 驅動迭代**:建評估集 → 量 baseline → **一次改一項** → 比指標 → 保留變好的、回退變壞的。

**追問**:檢索指標離線可算(放 CI);生成指標多靠 [LLM-as-judge](part28-llm-genai.md#q9-為什麼-llm-應用需要評估怎麼評)(要校準)。

---

## Q5.(必考)什麼是 ReAct agent?迴圈由誰驅動?

**考點**:agents([05-agents-react](../chapters/29-ai-applications/05-agents-react.md))

**答**:**ReAct = Reasoning + Acting**——**Thought(推理)→ Action(呼叫工具)→ Observation(結果)** 迴圈,**依觀察動態決定下一步**,直到完成:

```text
Thought → Action → Observation → Thought → ... → Final Answer
```

**迴圈由「你的程式」驅動**,不是模型——**模型只「請求」呼叫工具**,執行工具、回饋結果、控制迴圈的是你的程式(所以控制權在你,可設上限、攔截危險動作)。

**agent vs workflow**:流程要**模型動態決定** → agent;流程**固定** → workflow(**先選簡單的**,agent 貴/慢/難測)。

**追問**:**必設 `max_steps`**(防模型鬼打牆燒錢)+ **工具沙箱/最小權限/人工確認**(agent 跑的是模型決定的動作,信任邊界要嚴守)。

---

## Q6. MCP 是什麼?和 tool use 的關係?

**考點**:MCP([06-mcp](../chapters/29-ai-applications/06-mcp.md))

**答**:**MCP(Model Context Protocol)** 解決 **M×N 工具整合碎片化**——M 個 LLM 應用 × N 個工具,若各自實作就是 M×N 種整合。MCP 定義**標準協定**變成 **M+N**(像 USB-C)。

架構:**host / client / server**,基於 **JSON-RPC**,server 暴露 **tools/resources/prompts**。核心方法:**`tools/list`**(發現)、**`tools/call`**(呼叫),stdio/HTTP 傳輸。

**與 tool use 的關係**:MCP **動態提供工具定義**,轉成 [tool use](part28-llm-genai.md#q4-結構化輸出和-tool-use-差在哪tool-use-的循環) 給模型——**互補不取代**(MCP 是「工具從哪來」的標準,tool use 是「模型怎麼用」的機制)。

**追問**:安全——只連信任的 server、把 server 回傳當**不可信輸入**(防 [prompt injection](part30-production-ai.md#q5必考什麼是-prompt-injection為什麼比-sql-injection-難防))。

---

## Q7. 對話記憶怎麼管理?

**考點**:記憶管理([07-memory-context](../chapters/29-ai-applications/07-memory-context.md))

**答**:LLM **無狀態要送全歷史**(見 [Part 28 Q2](part28-llm-genai.md#q2-claude-messages-api-的形狀為什麼多輪對話要送完整歷史)),長對話會**撞 context 上限 + 成本暴漲 + 長 context 降品質**(lost in the middle)。

記憶策略:**全量**(短對話)、**滑動視窗**(保留最近 N 輪)、**摘要**(舊的壓成摘要)、**混合**(近期原文 + 遠期摘要,最常用)、**向量記憶**(歷史存向量庫,需要時檢索 = 對記憶做 RAG)。

**token 預算**:`system + 記憶 + 輸入 ≤ 上限`,且**預留輸出空間**;**先預留摘要額度**再填最近訊息。

**追問**:用**模型原生 tokenizer** 精算(Claude 用 `count_tokens`,**非 tiktoken**);別用「字元數/4」估。

---

## Q8. 什麼時候用多 agent?常見架構?

**考點**:多 agent([08-multi-agent](../chapters/29-ai-applications/08-multi-agent.md))

**答**:單 agent 的瓶頸:**工具太多易選錯、context 爆炸、責任不清、無法平行**。多 agent **分而治之**——每個 agent 專職、有聚焦的工具與 context。

常見架構:**orchestrator-worker(最常用)**、pipeline、平行+彙整、generator-critic。

**context 隔離的價值**:每 agent 有**乾淨聚焦的 context**(不互相污染),繞開單一 context 的容量上限。

**代價**:**成本/延遲疊加、更難除錯與預測**——**能用單 agent/workflow 解決就別上多 agent**。

**追問**:orchestrator 只分派彙整(不做事);獨立子任務可平行;設全系統成本上限。

---

## Q9. LangChain/LlamaIndex 這種框架解決什麼?有什麼取捨?

**考點**:框架([09-frameworks](../chapters/29-ai-applications/09-frameworks.md))

**答**:框架提供**統一模型介面、現成 RAG 元件與數百種整合、標準化管線/agent/記憶**——少寫膠水。

- **LangChain**:通用**編排**(+ LangGraph 建 agent 圖、LangSmith 觀測)。
- **LlamaIndex**:專精 **RAG/資料索引**。

**LCEL 的 `|`**:把 Runnable 元件串成管線(`prompt | model | parser`),一步輸出接下一步輸入。

**取捨**:快速起步/生態 vs **抽象洩漏、debug 難、API 變動快、黑箱**。

**追問**:**先懂原理(手刻過)再決定用框架**;簡單需求直接用官方 SDK、複雜整合/PoC 才上框架、關鍵路徑保留控制。

---

## Q10. 端到端 RAG 系統的架構?怎麼實現溯源?

**考點**:Capstone RAG([10-capstone-rag](../chapters/29-ai-applications/10-capstone-rag.md))

**答**:**離線(分塊 → embed → 索引)+ 線上(混合檢索 → 組裝 → 生成 → 溯源)+ 持續評估**。設計原則:**chunk 帶 metadata 貫穿全程、檢索與生成解耦、評估內建**。

**溯源**:**chunk 全程攜帶 source**(檔名/頁碼)——答案回傳來源供使用者驗證(生產級 RAG 的必要條件)。

**追問**:**從骨架到生產的差距**——真實 embedding/LLM(含[串流/重試](part30-production-ai.md))、ANN 索引、rerank、[快取/成本](part28-llm-genai.md#q8-llm-成本結構prompt-caching-怎麼省錢)、API 化、監控、[安全](part30-production-ai.md)(LLMOps)。

---

⬅️ [Part 28](part28-llm-genai.md) ｜ [索引](README.md) ｜ ➡️ [Part 30 生產級 AI 與 LLMOps](part30-production-ai.md)
