# exercises — 練習題

每題提供函式 stub 與測試，**實作前測試為紅燈**（設計如此），實作後應轉綠。

```text
exercises/
└── partNN/
    ├── <topic>.py         # 待你實作（stub）
    └── test_<topic>.py    # 測試（實作前紅燈）
```

執行：

```bash
pytest exercises        # 實作前部分紅燈，屬正常
```

參考解答見 [`../solutions/`](../solutions/)。

## 目前題目（依 Part 陸續補上）

| Part | 題目 |
|------|------|
| 1 入門 | `fizzbuzz`、`word_frequency` |
| 2 基礎 | `parameters`（args/kwargs）、`closures`、`comprehensions` |
| 3 資料結構 | `dict_ops`、`sequences`（保序去重/分塊）、`sorting_heap`（top-k/合併區間） |
| 4 OOP | `stack`、`shapes`（ABC/多型）、`temperature`（property） |
| 5 typing | `generics`（PEP 695）、`unique_by` |
| 6 錯誤處理 | `safe_ops`（try/except、EAFP）、`context_manager` |
| 7 迭代器/生成器 | `generators`（無限費氏/take）、`pipeline`（惰性分塊） |
| 8 函數式/裝飾器 | `decorators`（memoize）、`compose` |
| 9 併發 | `thread_safe_counter`（Lock）、`parallel_map`、`async_gather` |
| 11 標準庫 | `text_re`（re/slugify）、`collections_ex`（Counter）、`datetime_ex` |
| 14 Web | `app`（FastAPI:health/建立/查詢 + TestClient） |
| 15 資料庫 | `task_repo`（sqlite3 CRUD、參數化查詢） |
| 16 架構 | `repository`（Repository + Protocol）、`di`（依賴注入） |
| 17 資料處理 | `array_ops`（numpy 正規化/z-score）、`dataframe_ops`（pandas groupby） |
| 18 效能 | `algorithms`（two_sum O(n)、去重、first-unique） |
| 20 安全 | `password_hashing`（PBKDF2+salt）、`rate_limiter`（token bucket） |
| 22 分散式 | `idempotency`（冪等去重）、`consistent_hash`（一致性雜湊環） |
| 23 資料分析 | `sql_agg`（SQL GROUP BY） |
| 24 商業分析 | `stats`（描述統計/成長率） |
| 25 機器學習 | `classifier`（LogisticRegression 準確率） |
| 26 進階 ML | `metrics`（precision/recall） |
| 27 深度學習 | `nn`（sigmoid/relu/dense,numpy） |
| 28 LLM | `embeddings`（餘弦相似度/top-k 檢索） |
| 29 AI 應用 | `rag`（RRF 倒數排名融合） |
| 30 生產級 AI | `reliability`（指數退避） |

> 🚧 需第三方套件的 Part 已用 CI 內含的 `.[web,data]` 完成;需真實 LLM API(anthropic)的部分改以純邏輯練習呈現。剩餘偏概念的 Part(10 CPython 內部、12 測試、13 打包、19 雲原生、21 微服務、31 雲端部署)不適合「stub+測試」形式,暫略。
