# Python Engineering Handbook

> **From Zero to Senior Python Engineer**

一本從**完全沒接觸過 Python** 開始，逐步建立 **Python Engineering** 完整知識體系的工程手冊。

---

## 📖 About

大部分 Python 教材都從語法開始，學完 `list`、`dict`、簡單的 class 就結束了。

本書選擇走得更遠。

我們先理解：

- Python 為什麼這樣設計語言？
- 一切皆物件（everything is an object）到底是什麼意思？
- 為什麼有 GIL？它如何影響並發？
- CPython 的引用計數與 GC 如何管理記憶體？
- `decorator`、`generator`、`context manager` 背後的協定是什麼？

理解底層之後，再往上學習並發模型、Web、資料庫、資料處理、架構設計與部署，會發現許多設計其實都建立在相同的基礎之上。

因此，本書不是 API 文件，也不是面試題整理，而是一本完整的 **Python Engineering Handbook**。

---

## 🎯 目標

閱讀完本書後，你將能夠：

**Python 工程主線（Part 1–22）**

- 寫出符合慣例（idiomatic / Pythonic）的 Python 程式碼
- 理解 `list` / `dict` / `set` 的底層模型與 Python 物件模型
- 掌握並發：`threading` / GIL / `multiprocessing` / `asyncio`
- 理解 CPython：物件模型、引用計數、GC、bytecode、GIL 原理
- 用 `cProfile` 進行 Profiling 與效能優化
- 設計可維護的後端服務與專案架構（FastAPI + 分層）
- 進行雲原生部署（Docker / Kubernetes），並掌握微服務與分散式系統
- 通過 Senior Python Interview，成長為 Python Backend Architect

**資料 / AI / 部署主線（Part 23–31）**

- 掌握資料處理與分析生態（`numpy` / `pandas` / SQL / EDA / 統計與 A/B 測試）
- 建立機器學習與深度學習模型（scikit-learn、集成學習、PyTorch、CNN、注意力機制）
- 打造 LLM 應用：prompt engineering、tool use、embeddings、**RAG**、**AI agent**、MCP
- 把 AI 應用推上生產：LLMOps、可靠性、護欄、prompt injection 防禦、評估與資料飛輪
- 將服務部署上雲（AWS / GCP：容器、serverless、託管 DB、Terraform、OIDC CI/CD）

---

## 👥 適合對象

- 想學 Python 的初學者（不需要任何 Python 經驗）
- 從其他語言轉來的後端工程師
- Backend Engineer / Senior Backend Engineer
- Tech Lead / Architect
- Data / ML 工程師入門
- DevOps / SRE
- Computer Science 學生

---

## 📚 本書架構

全書共 **31 個 Part**，由語言基礎往上，逐步建立完整工程能力，分為兩條主線：

**Python 工程主線（Part 1–22）**——語言核心到分散式後端：

```text
Python 基礎 ──▶ 資料結構 ──▶ OOP ──▶ 型別系統 ──▶ 錯誤處理
   │
   ▼
迭代器/生成器 ──▶ 函數式/裝飾器 ──▶ 並發 ──▶ CPython 內部與記憶體
   │
   ▼
標準庫 ──▶ 測試 ──▶ 工程化/打包 ──▶ Web ──▶ 資料庫
   │
   ▼
架構 ──▶ 資料科學 ──▶ 效能優化 ──▶ 雲原生 ──▶ 安全與系統設計面試
   │
   ▼
微服務 ──▶ 分散式系統
```

**資料 / AI / 部署主線（Part 23–31）**——對應 Data Analyst / ML Engineer / AI Engineer 職位（以 Part 17 numpy/pandas 為前置）：

```text
資料分析(SQL/pandas) ──▶ 統計與商業分析 ──▶ 機器學習 ──▶ 進階 ML ──▶ 深度學習
   │
   ▼
LLM/GenAI ──▶ AI 應用(RAG/Agent) ──▶ 生產化 AI(LLMOps) ──▶ 雲端平台部署(AWS + GCP)
```

---

## 🐍 版本基準

本書的 Python 版本策略分三層，各章若用到特定版本特性會就地標註：

- **穩定教學基準：Python 3.12+** —— 全書範例、`examples/` 與 CI 都以 3.12+ 為準，可放心跟著跑。
- **前瞻章節：Python 3.13** —— free-threaded（no-GIL）建置、實驗性 JIT 等，於相關章節（並發、CPython 內部）以「前瞻／實驗」標註介紹，不作為預設基準。
- **實驗功能** —— 需特殊建置旗標或未來版本的特性，僅作概念說明，不用於可執行範例。

> AI 章節的模型 ID 與定價集中於 [Part 28 README 的模型參考表](chapters/28-llm-genai/README.md)，並附最後校正日期，避免散落各章難以維護。

---

## 📂 Repository Structure

```text
python-handbook/

├── README.md
├── CLAUDE.md              # 給 AI 協作者的專案規範
├── pyproject.toml         # 專案設定與依賴（examples/exercises/solutions/project 共用）
├── Makefile               # 常用指令入口（make test / lint / run / docker-build）
├── Dockerfile             # task-api 多階段建置（見 project/）
├── .github/workflows/     # CI：ruff + mypy + pytest
│
├── chapters/             # 各 Part 的章節內容（.md，31 Part）
├── project/              # 貫穿全書的實戰專案：task-api（FastAPI 分層服務，附測試）
├── examples/             # 可執行範例（pytest 驗證）
├── exercises/            # 練習題（stub + 測試，實作前為紅燈）
├── solutions/            # 練習解答（參考答案，全綠）
├── interview/            # Python 面試題庫
└── docs/                 # 設計文件與 spec
```

> **開發者用法**（已安裝 Python 3.12+）：
> ```bash
> pip install -e ".[dev]"                    # 安裝專案與開發依賴
> pytest project examples solutions          # 驗證「已完成」部分（應全綠）
> uvicorn project.app.main:app --reload      # 啟動實戰專案 task-api
> pytest exercises                           # 練習：實作前紅燈、實作後轉綠
> ruff check .   ；   mypy .                  # 靜態檢查與型別檢查
> ```
> 註：`exercises/` 的測試**預設紅燈**（待你實作），這是設計如此，別把它算進「壞掉」。

---

## 📖 Chapters

全書規劃 **31 個 Part**，由語言基礎一路到資料分析、機器學習、LLM/AI 與雲端部署：

> **可跑資源圖示**：📂 examples（可執行範例）｜ ✏️ exercises + solutions（練習與解答）｜ 🎯 interview（面試題庫）｜ 🏗️ project（task-api 實戰）

| #  | Part | 主題 |
|----|------|------|
| 1  | [入門 Getting Started](chapters/01-getting-started/) | Python 為何、安裝、直譯器、REPL、pip、venv、第一支程式、PEP 8、import 系統 |
| 2  | [語言基礎 Fundamentals](chapters/02-fundamentals/) | 動態型別、數值/字串/bool/None、運算子、流程控制、函式、`*args/**kwargs`、lambda、閉包、LEGB、推導式 |
| 3  | [資料結構 Data Structures](chapters/03-data-structures/) | list/tuple/dict/set/frozenset、切片、可變vs不可變、hashable、collections |
| 4  | [物件導向 OOP](chapters/04-oop/) | class、繼承、MRO、property、classmethod/staticmethod、魔術方法、dataclass、ABC |
| 5  | [型別系統 Typing](chapters/05-typing/) | type hints、typing 模組、TypeVar/Generic、Protocol、mypy |
| 6  | [錯誤處理 Error Handling](chapters/06-error-handling/) | exception、try/except/else/finally、自訂例外、例外鏈、context manager、with |
| 7  | [迭代器與生成器 Iterators & Generators](chapters/07-iterators-generators/) | iterable/iterator、yield、生成器表達式、itertools |
| 8  | [函數式與裝飾器 Functional & Decorators](chapters/08-functional-decorators/) | 高階函式、map/filter/reduce、decorator、functools、partial |
| 9  | [並發與並行 Concurrency](chapters/09-concurrency/) | threading、GIL、multiprocessing、concurrent.futures、asyncio/async-await、event loop |
| 10 | [CPython 內部與記憶體 CPython Internals & Memory](chapters/10-cpython-internals/) | 物件模型、引用計數、GC、記憶體管理、bytecode、GIL 原理 |
| 11 | [標準庫 Standard Library](chapters/11-stdlib/) | os/sys、pathlib、datetime、json、re、io、subprocess、logging |
| 12 | [測試 Testing](chapters/12-testing/) | unittest、pytest、fixture、mock、參數化、覆蓋率、TDD、doctest |
| 13 | [工程化與打包 Tooling & Packaging](chapters/13-tooling-packaging/) | pip、venv、uv/poetry、pyproject.toml、打包發佈、ruff/black、mypy、pre-commit |
| 14 | [Web 開發 Web Development](chapters/14-web/) | WSGI/ASGI、FastAPI/Flask、路由、middleware、REST、pydantic 驗證、認證 |
| 15 | [資料庫 Database](chapters/15-database/) | DB-API、sqlite3、SQLAlchemy ORM、連線池、transaction、migration、Redis |
| 16 | [架構與設計 Architecture](chapters/16-architecture/) | 分層、Clean Architecture、DI、Repository、SOLID、設計模式、專案結構 |
| 17 | [資料處理與科學計算 Data & Scientific Computing](chapters/17-data-science/) | numpy、pandas、資料清理、視覺化、Jupyter |
| 18 | [效能優化 Performance](chapters/18-performance/) | cProfile、優化、快取、Cython/numba、記憶體優化、非同步優化 |
| 19 | [雲原生與部署 Cloud Native](chapters/19-cloud-native/) | Docker、Gunicorn/Uvicorn、12-factor、CI/CD、Kubernetes、可觀測性 |
| 20 | [安全與系統設計面試 Security & System Design Interview](chapters/20-security-system-design/) | 輸入驗證、注入、認證授權、JWT、密鑰、OWASP、系統設計案例、Python 面試題庫 |
| 21 | [微服務 Microservices](chapters/21-microservices/) | gRPC、protobuf、服務發現、API gateway、健康檢查、限流與熔斷 |
| 22 | [分散式系統 Distributed Systems](chapters/22-distributed-systems/) | CAP、一致性、分散式鎖、訊息佇列、冪等、Saga、分散式追蹤 |
| 23 | [分析用 SQL 與資料整理 SQL & Data Wrangling](chapters/23-data-analysis/) | 分析師工作流、SQL 聚合/JOIN/window/CTE、pandas groupby/merge/樞紐、EDA、端到端分析 |
| 24 | [統計分析與商業洞察 Statistics & Business Analytics](chapters/24-business-analytics/) | 描述統計、相關與因果、假設檢定、A/B 統計、時間序列、cohort/funnel、視覺化、資料溝通 |
| 25 | [機器學習基礎 ML Foundations](chapters/25-machine-learning/) | ML 概論、train/test split、特徵工程、線性/邏輯回歸、模型評估、過擬合與正則化 |
| 26 | [進階機器學習 Advanced ML](chapters/26-advanced-ml/) | 決策樹、集成學習、k-means、PCA、超參數調校、類別不平衡、模型可解釋性 |
| 27 | [深度學習 Deep Learning](chapters/27-deep-learning/) | 神經網路、反向傳播、從零手刻 NN、PyTorch、CNN、注意力機制、訓練技巧 |
| 28 | [LLM 與生成式 AI LLM & GenAI](chapters/28-llm-genai/) | LLM 原理、Claude API、prompt engineering、tool use、串流、embeddings、向量資料庫、成本、評估 |
| 29 | [AI 應用工程 AI Application Engineering](chapters/29-ai-applications/) | RAG 全流程、chunking、混合檢索與 rerank、RAG 評估、ReAct agents、MCP、記憶、多 agent、框架 |
| 30 | [生產級 AI 與 LLMOps Production AI & LLMOps](chapters/30-production-ai/) | LLMOps、串流、可靠性、可觀測性、prompt injection、護欄/PII、eval gate、A/B、資料飛輪 |
| 31 | [雲端平台部署 Cloud Platform Deployment（AWS + GCP）](chapters/31-cloud-platform-deployment/) | AWS↔GCP 對照、IAM、容器/K8s/serverless、託管 DB/儲存、密鑰/網路、Terraform、OIDC 免金鑰 CI/CD、成本、上雲 Capstone |

> 各 Part 資料夾內有 README 索引（列出完整章節規劃）；每章彼此以「下一章」串接，可依序閱讀。
> ✅ 全 31 Part 內文與可執行範例皆已完成（`examples/` 附 `pytest` 驗證）。

---

## 💡 本書特色

不同於一般 Python 教材，本書採用由底向上的學習方式：

```text
Computer
   ↓
Programming Language
   ↓
Python Language Model（一切皆物件）
   ↓
CPython Interpreter & Runtime（引用計數 / GC / GIL / bytecode）
   ↓
Concurrency Model（threading / multiprocessing / asyncio）
   ↓
Standard Library
   ↓
Service / Web / Data
   ↓
Architecture & Deployment
```

每個章節都包含：

- **💡 白話導讀**（先用生活比喻把觀念講白，技術名詞後置——**每章必有，建議先讀**）
- **🎯 什麼時候會用到**（真實使用場景與決策訊號；抽象／理論章附上）
- **Why**（為什麼）
- **Theory**（理論）
- **Specification**（規範）
- **Implementation**（CPython 如何運作）
- **Code Example**（可執行的 Python 程式碼）
- **Diagram**（Mermaid 圖解）
- **Best Practice**（最佳實踐）
- **Common Mistakes**（常見誤解）
- **Interview Notes**（面試重點）

> 寫作原則：**詳盡 ≠ 密集**。每個抽象機制都配一個生活比喻（GIL＝餐廳只有一把菜刀、
> asyncio＝單人服務生、RAG＝開書考試），且比喻跨章沿用，建立一致的心智模型。

**每個 Part 以一章「統整」收尾**（`NN-summary.md`），把該 Part 所有章節收攏成一個整體：

- **🗺️ 知識地圖**——用 Mermaid 把整個 Part 串成一張圖，並找出貫穿全 Part 的**主軸**
  （例：Part 2 的 16 章其實都在講「變數是標籤，不是盒子」）。
- **⚡ 速查表**——「什麼情境用什麼」，日後可當工具書翻。
- **🔑 核心心智模型**——帶得走的幾句話。
- **🛠️ 小實作**——一支可執行的程式，同時用上該 Part 的多個章節。
- **✅ 自測清單**／**🎯 面試速查**——每題附回原章連結，答不出來直接跳回去。

> Part 23–31 已有 `NN-capstone-*.md`（整合**實作**專案），性質等同統整章。

---

## 🚀 如何使用

```bash
# 取得內容
git clone <repo-url>
cd python-handbook

# 建立虛擬環境並安裝
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 驗證可執行範例（exercises/ 為練習用，故意紅燈，不納入）
pytest project examples solutions
ruff check .
mypy .

# 或用 Makefile（Linux/macOS，或 Windows 自備 make）
make test        # 跑測試
make lint        # ruff + mypy
make run         # 啟動 task-api
make docker-build
```

依 Part 順序閱讀即可；若已有經驗，也可直接跳到對應 Part。

---

## 📄 License

MIT License
