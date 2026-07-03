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

- 寫出符合慣例（idiomatic / Pythonic）的 Python 程式碼
- 理解 `list` / `dict` / `set` 的底層模型與 Python 物件模型
- 掌握並發：`threading` / GIL / `multiprocessing` / `asyncio`
- 理解 CPython：物件模型、引用計數、GC、bytecode、GIL 原理
- 用 `cProfile` 進行 Profiling 與效能優化
- 設計可維護的後端服務與專案架構（FastAPI + 分層）
- 掌握資料處理生態（`numpy` / `pandas`）
- 進行雲原生部署（Docker / Kubernetes）
- 通過 Senior Python Interview
- 成長為 Python Backend Architect

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

由語言基礎往上，逐步建立完整工程能力：

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
```

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
├── chapters/             # 各 Part 的章節內容（.md，20 Part）
├── project/              # 貫穿全書的實戰專案：task-api（FastAPI 分層服務，附測試）
├── examples/             # 可執行範例（pytest 驗證）
├── exercises/            # 練習題（stub + 測試，實作前為紅燈）
├── solutions/            # 練習解答（參考答案，全綠）
└── interview/            # Python 面試題庫
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

全書規劃 **22 個 Part**，由語言基礎往上：

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

> 各 Part 資料夾內有 README 索引（列出完整章節規劃）；每章彼此以「下一章」串接，可依序閱讀。
> ✅ 全 22 Part 內文與可執行範例皆已完成（`examples/` 附 `pytest` 驗證）。

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

- **Why**（為什麼）
- **Theory**（理論）
- **Specification**（規範）
- **Implementation**（CPython 如何運作）
- **Code Example**（可執行的 Python 程式碼）
- **Diagram**（Mermaid 圖解）
- **Best Practice**（最佳實踐）
- **Common Mistakes**（常見誤解）
- **Interview Notes**（面試重點）

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
