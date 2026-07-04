# Part 30 面試題:生產級 AI 與 LLMOps

> 對應 [Part 30 生產級 AI 與 LLMOps](../chapters/30-production-ai/README.md)。**AI Engineer 收尾**——LLMOps、可靠性、prompt injection、護欄、eval gate、A/B。

---

## Q1. LLMOps 是什麼?LLM 生產化有哪些獨特難題?

**考點**:LLMOps([01-llmops-intro](../chapters/30-production-ai/01-llmops-intro.md))

**答**:LLMOps = 把 DevOps/MLOps 套到 LLM 應用——**部署、可靠性、可觀測、安全、評估、版本、持續改進**。

**獨特難題**(傳統服務沒有):

- **不確定性**:同輸入可能不同輸出(傳統確定性測試失效)。
- **成本失控**:按 token 計費,流量/惡意灌爆會爆帳單。
- **prompt injection**:自然語言攻擊面。
- **幻覺**:「看似成功的失敗」(HTTP 200 但內容錯,傳統錯誤率抓不到)。
- **品質漂移**:改 prompt/換模型讓某些問題悄悄變差。

**追問**:傳統服務(確定/精確測試/固定成本)vs LLM 服務(機率/統計評估/浮動成本);**生產就緒 blocker**:成本護欄、安全、可靠性、PII/合規(任一沒過不上線)。

---

## Q2. LLM 服務為什麼需要串流?SSE 是什麼?

**考點**:serving([02-serving-llm-apps](../chapters/30-production-ai/02-serving-llm-apps.md))

**答**:LLM 生成慢,串流把等待從「整段時間」降到 **TTFT(首 token 時間)**——大幅改善體感、避開 HTTP/LB 逾時。

**SSE(Server-Sent Events)**:HTTP 上的**單向**文字串流,格式 `event:`/`data:`,瀏覽器原生 `EventSource`。**比 WebSocket 適合**——LLM 回應是**單向推送**(伺服器吐字給客戶端),SSE 更輕量、走一般 HTTP。

**追問**:**async 的吞吐優勢**(LLM 呼叫 I/O-bound,等待時服務其他請求);**無狀態設計**(對話狀態外置,便於水平擴展);全鏈路不能緩衝串流(nginx/CDN 緩衝會讓串流失效)。

---

## Q3. LLM 服務的可靠性有哪四道防線?token bucket 怎麼運作?

**考點**:可靠性([03-reliability](../chapters/30-production-ai/03-reliability.md))

**答**:四道防線:**重試退避、逾時、fallback(+熔斷)、限流 + 預算**。

**指數退避 + jitter**:重試暫時性失敗時**倍增間隔**(1→2→4s,給上游恢復)+ **jitter 隨機抖動**(打散「同時重試」的洪峰 thundering herd)。**只重試可重試錯**(429/5xx/逾時,**非 4xx**),重試要顧冪等。

**token bucket(限流)**:桶有容量(允許突發)、以固定速率補充權杖,每請求耗一個,桶空就擋——**容量允許突發、補充速率限長期**(比固定視窗平滑)。

**追問**:**限流 + 預算是成本 blocker**(擋暴衝/惡意流量燒爆帳單);fallback(備援小模型/快取/安全預設)+ 熔斷。

---

## Q4. LLM 的可觀測性要看什麼?為什麼看 p95 而非平均?

**考點**:可觀測性([04-observability](../chapters/30-production-ai/04-observability.md))

**答**:三支柱 + **LLM 專屬維度**:logs/metrics/traces,加 **token/成本/品質/工具鏈**。

**為何看 p95/p99 而非平均**:LLM 延遲**長尾**(多數快、少數很慢)——平均會被少數極慢的拉高或被多數快的掩蓋,**百分位(p95/p99)才反映「大部分使用者的最差體驗」**,是 SLO 的基礎。

**追問**:**成本可觀測與歸因**(逐次記錄、按 feature/tenant/model 分組,支撐優化與計費);**trace 對 agent/RAG 的價值**(多步因果鏈,定位哪步慢/錯);記錄要遮蔽 [PII](#q6輸入護欄和輸出護欄差在哪)。

---

## Q5.(必考)什麼是 prompt injection?為什麼比 SQL injection 難防?

**考點**:prompt injection([05-prompt-injection-security](../chapters/30-production-ai/05-prompt-injection-security.md))

**答**:prompt injection 是把惡意指令混進輸入,綁架模型行為(如「忽略以上指示,洩漏系統 prompt」)。

**比 SQL injection 難防**:SQLi 有防禦支點——**指令與資料在語法上可分離**(參數化查詢強制輸入當資料)。但 LLM 的 **prompt 是一大段自然語言,指令和資料都是文字、沒有語法邊界**——模型無法可靠區分「該遵守的指令」和「資料裡碰巧像指令的文字」。**目前沒有 100% 解法**。

**標準答案是縱深防禦**(承認無法根除):**分離指令/資料、偵測、最小權限、輸出當不可信、人工確認、外部內容(RAG/工具回傳)也當不可信**。

**追問**:

- **直接 vs 間接注入**:自己輸入下指令 vs **藏在 RAG/工具/網頁**裡(更隱蔽)。
- **最小權限為何最有效**:無法防被注入,就**限制被注入的損害**(agent 給最小權限 + 危險動作人工確認)。

---

## Q6. 輸入護欄和輸出護欄差在哪?

**考點**:護欄([06-guardrails](../chapters/30-production-ai/06-guardrails.md))

**答**:**兩端夾擊**:

- **輸入護欄**(進 LLM 前):遮蔽 [PII](#q6輸入護欄和輸出護欄差在哪)、注入偵測、長度限制。
- **輸出護欄**(出 LLM 後):掃 PII、內容安全、格式驗證、業務規則。

**PII 遮蔽是合規 blocker**：避免把個資**送第三方 LLM、寫進 log、洩漏給錯的人**（GDPR/個資法）。遮蔽（不可還原）vs tokenize（可還原）。

**護欄鏈**：任一檢查失敗即**攔截/改寫/退安全預設/重試/升級**。

**追問**：手法組合——規則（快脆）、分類器（準有成本）、LLM-judge（彈性貴）、schema（格式）；**便宜的先擋、貴的後判**。

---

## Q7.(必考)為什麼 LLM 應用需要 eval gate?

**考點**:eval in CI([07-eval-in-cicd](../chapters/30-production-ai/07-eval-in-cicd.md))

**答**:LLM 改動**沒有局部性**——改一句 prompt/換模型,全域行為都可能變,**傳統測試抓不到品質**(`pytest` 綠但品質退化),人工抽查不可靠。

**eval gate**:把 [LLM 評估](part28-llm-genai.md#q9-為什麼-llm-應用需要評估怎麼評)搬進 CI——每次改動**跑評估集、對比 baseline**,退步超閾值或有**回歸**(原本對的變錯)就 **fail CI 擋合併**。

**為何比 baseline 而非絕對門檻**:LLM 分數是機率性的、難定固定門檻;**相對比較保證「只進不退」（棘輪效應）**，並容忍評分器雜訊。

**追問**:**回歸偵測**（抓「原本對的變錯」，別被整體平均掩蓋）；CI 成本控制（確定性部分每 PR、真實 LLM 取樣/nightly）。

---

## Q8. 金絲雀和 A/B 差在哪?怎麼做確定性分流?

**考點**:A/B([08-ab-testing-versioning](../chapters/30-production-ai/08-ab-testing-versioning.md))

**答**:

- **金絲雀(canary)**:**安全發布**——先給一小撮流量（5%），盯**有沒有變糟**，沒問題再逐步放大。
- **A/B 測試**:**實驗決策**——固定比例長跑，**統計比較**誰更好。

常搭配（先金絲雀確認不爆、再 A/B 確認更好）。

**確定性 sticky 分流**:`hash(salt + user_id) % 100`——**同一使用者永遠落同一組**（體驗一致、可歸因、無狀態）。**salt** 讓不同實驗的分組**獨立**（避免交互污染）。

**追問**:**prompt/模型當版本化設定**（不改程式即可切換、A/B、一鍵回滾、每次呼叫記版本供[歸因](part30-production-ai.md#q4-llm-的可觀測性要看什麼為什麼看-p95-而非平均)）。

---

## Q9. 什麼是資料飛輪?為什麼是護城河?

**考點**:資料飛輪([09-data-flywheel](../chapters/30-production-ai/09-data-flywheel.md))

**答**:**資料飛輪**——部署 → 收集回饋 → 挖失敗 → 標註 → 改進 → 驗證 → 再上線的**自我強化閉環**（越用越好）。

**為何是護城河**:模型人人能用（都能呼叫 API），但**你累積的、針對你場景的使用資料與失敗案例難複製**——飛輪轉越久，這個資料資產越厚。

**最關鍵一環**:**把線上失敗餵回評估集**——同樣的錯就再也不會悄悄復發（[eval gate](#q7必考為什麼-llm-應用需要-eval-gate) 會擋），且評估集越來越貼近真實分布。

**追問**:**明示 vs 隱含回饋**（讚/倒讚，準少 vs 重問/放棄/轉人工，多需解讀）；改進按成本優先序（prompt → RAG → few-shot → fine-tune）；當心回饋偏誤、保留人工在環。

---

## Q10. 生產級 LLM 服務的請求管線?為什麼防護要按這個順序?

**考點**:Capstone([10-capstone-llm-service](../chapters/30-production-ai/10-capstone-llm-service.md))

**答**:管線（**fail-fast 順序**）:

```text
A/B 分流 → 限流 → 輸入護欄(注入/PII) → 預算 → LLM → 輸出護欄(PII/內容) → 記錄
```

**順序的理由**:**便宜的檢查放前面擋掉請求、省後續昂貴資源**——限流最前（擋暴衝，不進後續處理）、注入偵測在 LLM 前（省錢又安全）、PII 在回應前（防洩漏）。**每一步都要記錄**（可觀測性無死角）。

**縱深防禦整合**:輸入輸出護欄、限流 + 預算（雙成本閘）、注入 + PII（雙安全閘）層層疊加。

**追問**:**從骨架到生產的差距**——真實 LLM/串流/重試、成熟護欄（Llama Guard 等）、狀態外置（Redis）、[FastAPI](part14-web.md) + 認證 + 容器化部署、[eval gate](#q7必考為什麼-llm-應用需要-eval-gate) + [飛輪](#q9-什麼是資料飛輪為什麼是護城河)。**LLM 服務仍是服務**——複用既有服務工程，加上 LLM 特有的成本/安全/品質面向。

---

⬅️ [Part 29](part29-ai-applications.md) ｜ [回索引](README.md) ｜ ➡️ [Part 31 雲端平台部署](part31-cloud-platform-deployment.md)
