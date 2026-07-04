# Part 28 面試題:LLM 與生成式 AI

> 對應 [Part 28 LLM 與生成式 AI](../chapters/28-llm-genai/README.md)。**AI Engineer 核心**——LLM 原理、prompt、tool use、embeddings、向量庫、成本。

---

## Q1.(必考)LLM 怎麼生成文字?temperature 在做什麼?

**考點**:LLM 原理([01-llm-fundamentals](../chapters/28-llm-genai/01-llm-fundamentals.md))

**答**:LLM 是**自迴歸**的——**逐 token** 預測「下一個 token 的機率分布」,取樣一個,再把它接上去預測下一個。**不是查表、也非真正理解**(所以會**幻覺**——沒把握時仍產生看似合理的 token)。

**temperature**:控制取樣的隨機性——把 logits **除以 T 再 softmax**:

- **低溫(T→0)**:分布尖銳 → 選最可能的 → **穩定、確定**(T=0 等同貪婪)。
- **高溫**:分布平坦 → 更隨機 → **多樣、發散**。

**追問**:**token**(文字的最小單位)——**成本/長度/速度都以 token 計**;**context window**(一次能吃的 token 上限);top-k/top-p(截掉長尾低機率 token)。

---

## Q2. Claude Messages API 的形狀?為什麼多輪對話要送完整歷史?

**考點**:呼叫 API([02-calling-llm-api](../chapters/28-llm-genai/02-calling-llm-api.md))

**答**:Messages API——`messages` 陣列(user/assistant **交替**)、`system` 參數(角色指令)、`content` 是 **block 陣列**、回應含 `stop_reason`、`usage`(token 數)。

**API 無狀態 → 多輪對話要送完整歷史**:模型**不記得**上一輪,每次呼叫都要把**整段對話**送回去——所以對話越長、輸入 token 越多、**成本隨對話長度增長**(見 [Part 29 記憶管理](part29-ai-applications.md#q7對話記憶怎麼管理))。

**追問**:`content` 是 block 陣列,要**遍歷找 text block**(別假設 `content[0]`);用官方 SDK、金鑰走環境變數、型別化例外 + 自動重試;算 token 用 Claude 的 `count_tokens`(**別用 tiktoken**——那是 OpenAI 的)。

---

## Q3. 有效的 prompt 技巧有哪些?few-shot 和 CoT 為什麼有效?

**考點**:prompt engineering([03-prompt-engineering](../chapters/28-llm-genai/03-prompt-engineering.md))

**答**:技巧:**清晰指令、system 角色、few-shot(給範例)、CoT(思維鏈)、任務分解、結構化輸出**。

- **few-shot 為何有效**:**in-context learning**——模型從 prompt 裡的**範例模式**現學(不改權重),推斷你要的格式/風格。
- **CoT(chain-of-thought)為何提升推理**:讓模型**展開中間步驟**——這些步驟成為後續生成的脈絡,本質是**給模型更多「思考 token」**(邊寫邊想)。

**追問**:system(穩定角色/規則)vs user(具體任務)的分工。

---

## Q4. 結構化輸出和 tool use 差在哪?tool use 的循環?

**考點**:結構化輸出/tool use([04-structured-output-tools](../chapters/28-llm-genai/04-structured-output-tools.md))

**答**:

- **結構化輸出**:讓模型回**可解析的 JSON**(給下游程式用)。
- **tool use(function calling)**:讓模型**呼叫工具執行動作**(查 DB、算數、呼叫 API)。

**tool use 多步循環**:定義工具 → 模型回 **`tool_use`**(要呼叫哪個工具 + 參數)→ **你的程式執行工具** → 把結果當 **`tool_result`** 回饋 → 模型據此回答。

**追問**:**「模型建議、程式執行」的安全分界**——模型只**請求**呼叫工具,執行與否由你決定(對副作用操作加保護,防 [prompt injection](part30-production-ai.md#q5必考什麼是-prompt-injection為什麼比-sql-injection-難防));工具的 `description` 是模型決策的依據。

---

## Q5. 串流解決什麼?為什麼 async 適合 LLM 服務?

**考點**:串流/async([05-streaming-async](../chapters/28-llm-genai/05-streaming-async.md))

**答**:串流解決**體感延遲**——LLM 生成慢,串流讓文字**逐字浮現**,把等待從「整段生成時間」降到 **TTFT(首 token 時間)**,還能**防大請求逾時**(連線持續有資料)。

**TTFT vs 總生成時間**:串流縮短**前者(感知延遲)**,不改後者(總時間)。機制:**SSE**(逐 delta 事件)。

**async 適合 LLM 服務**:LLM 呼叫是 **I/O-bound**(大部分時間在等模型),async 讓單執行緒在**等待時服務其他請求**(大量並發等待中的請求),吞吐遠勝同步。

**追問**:見 [Part 30 serving](part30-production-ai.md#q2-llm-服務為什麼需要串流sse-是什麼)。

---

## Q6.(必考)embedding 是什麼?餘弦相似度?語意搜尋流程?

**考點**:embeddings([06-embeddings-semantic-search](../chapters/28-llm-genai/06-embeddings-semantic-search.md))

**答**:**embedding** 是把文字轉成**捕捉語意的向量**——**語意相近的文字,向量也相近**(從資料學出的表示)。

**餘弦相似度**:兩向量夾角的餘弦(範圍 −1~1)——**只看方向(語意),忽略長度**(文字長短)。越接近 1 越相似。

**語意搜尋流程**:離線把文件都 embed 存起來 → 查詢也 embed → 算查詢與各文件的餘弦相似度 → 取 **top-k** 最相似。

**追問**:**語意搜尋 vs 關鍵字搜尋**互補——語意(意思相近,「退貨」對應「退換貨」)vs 關鍵字(字面精確,產品型號);實務用**混合檢索**(見 [Part 29](part29-ai-applications.md#q3混合檢索的動機rrf-融合))。

---

## Q7. 向量資料庫做什麼?精確和近似最近鄰(ANN)差在哪?

**考點**:向量資料庫([07-vector-databases](../chapters/28-llm-genai/07-vector-databases.md))

**答**:向量資料庫**存大量向量 + ANN 索引快速找最相似 + 中繼資料過濾**——是語意搜尋/RAG 的**檢索引擎**。

- **精確最近鄰**:和每個向量比 → **O(n)**——資料一大就慢。
- **ANN(近似最近鄰)**:**次線性**——犧牲一點召回率換速度(HNSW 等演算法用多層圖導航,只查一小部分向量)。

**追問**:HNSW(多層圖導航);**向量正規化後,點積 = 餘弦**(加速比較);pgvector/Chroma/FAISS/Pinecone 等。

---

## Q8. LLM 成本結構?prompt caching 怎麼省錢?

**考點**:成本([08-cost-latency-caching](../chapters/28-llm-genai/08-cost-latency-caching.md))

**答**:成本 = **輸入 token × 單價 + 輸出 token × 單價**——**輸出更貴**(Claude 約 5:1),不同模型差數倍(Opus vs Haiku)。

**prompt caching**:快取**重複的前綴**(前綴比對)——之後重用只要 **~0.1× 成本**。把**穩定內容放前面**(system prompt、長文件、few-shot 範例),變動的放後面。**省 70–90%**。

**模型分流**:依任務難度選模型(簡單用 Haiku、難的用 Opus)——適材適所省成本。

**追問**:**prompt caching**(快取前綴的**處理**,仍呼叫 API)vs **應用層/語意快取**(相同/相似查詢**免呼叫**),兩者不同。

---

## Q9. 為什麼 LLM 應用需要評估?怎麼評?

**考點**:評估([09-evaluation](../chapters/28-llm-genai/09-evaluation.md))

**答**:LLM 輸出**非確定、開放**——「跑幾個問題看起來還行」不可靠,改一句 prompt/換模型的效果**不可預測**(可能某些變好某些變壞)。要**量化評估**。

**評分方法**:規則/精確匹配(客觀但僵)、語意相似度、**LLM-as-judge**(用另一個 LLM 打分,彈性但有成本/偏誤)、人工(準但貴)。

**eval 驅動開發**:改動前後**跑評估集比分數**,升了才採用;**接 CI 防迴歸**(見 [Part 30](part30-production-ai.md#q6必考為什麼-llm-應用需要-eval-gate))。

**追問**:LLM-as-judge 的 rubric 要**具體**(否則評審也會偏),用人工標註校準、固定 judge 版本。

---

⬅️ [Part 27](part27-deep-learning.md) ｜ [索引](README.md) ｜ ➡️ [Part 29 AI 應用工程](part29-ai-applications.md)
