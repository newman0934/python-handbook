# Python Handbook — 章節總覽

> 全書共 **31 個 Part**,由語言基礎往上逐步建立完整工程能力,分兩條主線:
>
> - **Python 工程主線(Part 1–22)**:語言核心 → 型別/錯誤處理 → 迭代/函數式 → 並發 → CPython 內部 → 標準庫/測試/打包 → Web/資料庫 → 架構 → 微服務/分散式。
> - **資料 / AI / 部署主線(Part 23–31)**:資料分析 → 統計與商業分析 → 機器學習 → 深度學習 → LLM/RAG/Agent → 生產化 AI(LLMOps)→ 雲端平台部署,對應 Data Analyst / ML Engineer / AI Engineer 職位。

| # | Part | 章數 | 主題 |
|---|------|------|------|
| 1 | [入門 Getting Started](01-getting-started/) | 13 | 從零開始：認識 Python、把開發環境準備好、理解 Python 怎麼被執行。 |
| 2 | [語言基礎 Fundamentals](02-fundamentals/) | 17 | 動態型別、基本型別、運算子、流程控制、函式與作用域——寫任何 Python 的地基。 |
| 3 | [資料結構 Data Structures](03-data-structures/) | 13 | list / tuple / dict / set 的用法與底層模型，可變性與 hashable。 |
| 4 | [物件導向 OOP](04-oop/) | 16 | class、繼承、MRO、property 與魔術方法——Python 的物件模型。 |
| 5 | [型別系統 Typing](05-typing/) | 12 | type hints、typing 模組、泛型與 Protocol，配合 mypy 做靜態型別檢查。 |
| 6 | [錯誤處理 Error Handling](06-error-handling/) | 12 | exception 機制、try/except、自訂例外與 context manager。 |
| 7 | [迭代器與生成器 Iterators & Generators](07-iterators-generators/) | 8 | iterable / iterator 協定、generator 與 yield、itertools。 |
| 8 | [函數式與裝飾器 Functional & Decorators](08-functional-decorators/) | 7 | 高階函式、decorator 原理與 functools。 |
| 9 | [並發與並行 Concurrency](09-concurrency/) | 13 | threading、GIL、multiprocessing、asyncio——Python 的並發全貌。 |
| 10 | [CPython 內部與記憶體 CPython Internals & Memory](10-cpython-internals/) | 11 | 物件模型、引用計數、GC、bytecode、GIL 原理——理解 Python 為何這樣跑。 |
| 11 | [標準庫 Standard Library](11-stdlib/) | 17 | os / pathlib / datetime / json / re / logging 等日常必備標準庫。 |
| 12 | [測試 Testing](12-testing/) | 11 | unittest、pytest、fixture、mock、覆蓋率與 TDD。 |
| 13 | [工程化與打包 Tooling & Packaging](13-tooling-packaging/) | 9 | pip、venv、uv/poetry、pyproject.toml、打包發佈與 lint/format。 |
| 14 | [Web 開發 Web Development](14-web/) | 18 | WSGI/ASGI、FastAPI/Flask、REST API、pydantic 驗證與認證。 |
| 15 | [資料庫 Database](15-database/) | 25 | **原理篇**:關聯模型、SQL 語意、正規化、儲存/索引/優化器、交易並發(MVCC)、WAL、複製分片、NoSQL 選型;**實作篇**:DB-API、SQLAlchemy、連線池、transaction、migration、Redis、async、N+1、索引、PostgreSQL 專屬(JSONB/UPSERT/GIN)、多資料庫對照、MySQL 專屬(InnoDB/utf8mb4)、MongoDB 文件建模(embed vs reference)。 |
| 16 | [架構與設計 Architecture](16-architecture/) | 11 | 分層、Clean Architecture、DI、Repository、SOLID 與設計模式。 |
| 17 | [資料處理與科學計算 Data & Scientific Computing](17-data-science/) | 9 | numpy、pandas、資料清理與視覺化——Python 生態的殺手級應用。 |
| 18 | [效能優化 Performance](18-performance/) | 7 | profiling、快取、Cython/numba 與記憶體優化。 |
| 19 | [雲原生與部署 Cloud Native](19-cloud-native/) | 8 | Docker、Gunicorn/Uvicorn、12-factor、CI/CD、Kubernetes 與可觀測性。 |
| 20 | [安全與系統設計面試 Security & System Design Interview](20-security-system-design/) | 15 | 輸入驗證、注入、認證授權、密鑰管理，以及系統設計案例與 Python 面試題庫。 |
| 21 | [微服務 Microservices](21-microservices/) | 8 | gRPC、服務發現、API gateway、限流與熔斷——Python 的微服務實務。 |
| 22 | [分散式系統 Distributed Systems](22-distributed-systems/) | 8 | CAP、一致性、分散式鎖、訊息佇列、冪等、Saga 與分散式追蹤。 |

### 資料 / AI / 部署主線(Part 23–31)

| # | Part | 章數 | 主題 |
|---|------|------|------|
| 23 | [分析用 SQL 與資料整理 SQL & Data Wrangling](23-data-analysis/) | 9 | 分析師工作流、SQL 聚合/JOIN/window/CTE、pandas groupby/merge/樞紐、EDA、端到端分析。 |
| 24 | [統計分析與商業洞察 Statistics & Business Analytics](24-business-analytics/) | 9 | 描述統計、相關與因果、假設檢定、A/B 統計、時間序列、cohort/funnel/retention、視覺化、資料溝通、商業分析報告。 |
| 25 | [機器學習基礎 ML Foundations](25-machine-learning/) | 8 | ML 概論、工作流與 train/test split、特徵工程、線性/邏輯回歸、模型評估、過擬合與正則化、端到端 ML 專案。 |
| 26 | [進階機器學習 Advanced ML](26-advanced-ml/) | 8 | 決策樹、集成學習(隨機森林/梯度提升)、k-means 聚類、PCA 降維、超參數調校、類別不平衡、模型可解釋性、進階 ML 專案。 |
| 27 | [深度學習 Deep Learning](27-deep-learning/) | 8 | 神經網路基礎、反向傳播與梯度下降、從零手刻 NN、PyTorch 框架、CNN、注意力機制、訓練技巧、從零訓練通用網路。 |
| 28 | [LLM 與生成式 AI 基礎 LLM & GenAI](28-llm-genai/) | 9 | LLM 原理、呼叫 Claude API、prompt engineering、tool use、串流、embeddings、向量資料庫、成本優化、評估。 |
| 29 | [AI 應用工程 AI Application Engineering](29-ai-applications/) | 10 | RAG 全流程、chunking、混合檢索與 rerank、RAG 評估、ReAct agents、MCP、對話記憶、多 agent、應用框架、生產級 RAG Capstone。 |
| 30 | [生產級 AI 與 LLMOps Production AI & LLMOps](30-production-ai/) | 10 | LLMOps、API 化與串流、可靠性、可觀測性、prompt injection、護欄/PII、評估回歸 CI、A/B 與版本管理、資料飛輪、生產級 LLM 服務 Capstone。 |
| 31 | [雲端平台部署 Cloud Platform Deployment(AWS + GCP)](31-cloud-platform-deployment/) | 11 | AWS↔GCP 對照、IAM、容器(ECS/Fargate vs Cloud Run)、K8s(EKS vs GKE)、Serverless、託管 DB/物件儲存、密鑰/網路、Terraform、OIDC 免金鑰 CI/CD、可觀測性/成本、task-api 端到端上雲 Capstone。 |

[⬆️ 回專案首頁](../README.md)
