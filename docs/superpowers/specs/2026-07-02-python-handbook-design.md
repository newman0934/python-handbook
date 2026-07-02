# Python Engineering Handbook — 設計文件（Spec）

> 日期：2026-07-02
> 參考來源：`newman0934/golang-handbook`（本機 `../golang-handbook`）
> 定位：一本從「完全沒接觸 Python」到「Senior Python 工程師 / 架構師」的工程手冊。

---

## Overview（總覽）

本專案是一本 **Python 學習手冊**，內容主體為 Markdown 章節（`.md`），非應用程式。
沿用 golang-handbook 的「**由底層往上**」教學理念：先理解語言模型與 CPython 執行機制，
再往上到框架、資料處理、架構與部署。並採 **Python 原生改編**：保留 20 Part 骨架與固定章節模板，
但將 Go 專屬主題（goroutine/channel、GMP、GC runtime）替換為 Python 對應主題
（GIL/asyncio、CPython 內部與引用計數 GC）。

- 說明語言：繁體中文（zh-TW）。
- 維持英文：程式碼、套件/型別/函式名稱、API 路徑、技術專有名詞（GIL、asyncio、decorator…）、commit 格式。

## Business Requirements（目標）

讀完本書，讀者應能：

- 寫出符合慣例（idiomatic / Pythonic）的 Python 程式碼
- 理解 list/dict/set 的底層模型與物件模型
- 掌握並發：threading / GIL / multiprocessing / asyncio
- 理解 CPython：物件模型、引用計數、GC、bytecode、GIL 原理
- 用 cProfile 進行 profiling 與效能優化
- 設計可維護的後端服務與專案架構（FastAPI + 分層）
- 掌握資料處理生態（numpy / pandas）
- 進行雲原生部署（Docker / Kubernetes）
- 通過 Senior Python Interview

## 適合對象

Python 初學者、從其他語言轉來的後端工程師、Backend / Senior Backend、Tech Lead / Architect、
Data / ML 工程師入門、DevOps / SRE、CS 學生。

---

## Functional Requirements（功能需求）

### 章節模板（每章固定，順序固定，依需要增減區塊）

```markdown
# <章節標題>

> 一句話點出本章重點。

## Why（為什麼）
## Theory（理論）
## Specification（規範 / 語言定義）
## Implementation（底層如何運作）
## Code Example（可執行的 Python 範例）
## Diagram（Mermaid 圖解）
## Best Practice（最佳實踐）
## Common Mistakes（常見誤解）
## Interview Notes（面試重點）

---

➡️ 下一章：[<下一章標題>](<NN-next>.md)

[⬆️ 回 Part N 索引](README.md)
```

### 20 個 Part（Python 原生改編）

| #  | Part（資料夾）| 主題 |
|----|------|------|
| 1  | 入門 `01-getting-started` | Python 為何、安裝、直譯器、REPL、pip、venv、第一支程式、PEP 8、import 系統 |
| 2  | 語言基礎 `02-fundamentals` | 動態型別、數值/字串/bool/None、運算子、流程控制、函式、`*args/**kwargs`、lambda、閉包、LEGB、推導式 |
| 3  | 資料結構 `03-data-structures` | list/tuple/dict/set/frozenset、切片、可變vs不可變、hashable、collections |
| 4  | 物件導向 `04-oop` | class、繼承、MRO、property、classmethod/staticmethod、魔術方法、dataclass、ABC |
| 5  | 型別系統 `05-typing` | type hints、typing 模組、TypeVar/Generic、Protocol、mypy |
| 6  | 錯誤處理 `06-error-handling` | exception、try/except/else/finally、自訂例外、例外鏈、context manager、with |
| 7  | 迭代器與生成器 `07-iterators-generators` | iterable/iterator、yield、生成器表達式、itertools |
| 8  | 函數式與裝飾器 `08-functional-decorators` | 高階函式、map/filter/reduce、decorator、functools、partial |
| 9  | 並發與並行 `09-concurrency` | threading、GIL、multiprocessing、concurrent.futures、asyncio/async-await、event loop |
| 10 | CPython 內部與記憶體 `10-cpython-internals` | 物件模型、引用計數、GC、記憶體管理、bytecode、GIL 原理 |
| 11 | 標準庫 `11-stdlib` | os/sys、pathlib、datetime、json、re、io、subprocess、logging |
| 12 | 測試 `12-testing` | unittest、pytest、fixture、mock、參數化、覆蓋率、TDD、doctest |
| 13 | 工程化與打包 `13-tooling-packaging` | pip、venv、uv/poetry、pyproject.toml、打包發佈、ruff/black、mypy、pre-commit |
| 14 | Web 開發 `14-web` | WSGI/ASGI、FastAPI/Flask、路由、middleware、REST、pydantic 驗證、認證 |
| 15 | 資料庫 `15-database` | DB-API、sqlite3、SQLAlchemy ORM、連線池、transaction、migration、Redis |
| 16 | 架構與設計 `16-architecture` | 分層、Clean Architecture、DI、Repository、SOLID、設計模式、專案結構 |
| 17 | 資料處理與科學計算 `17-data-science` | numpy、pandas、資料清理、視覺化、Jupyter |
| 18 | 效能優化 `18-performance` | cProfile、優化、快取、Cython/numba、記憶體優化、非同步優化 |
| 19 | 雲原生與部署 `19-cloud-native` | Docker、Gunicorn/Uvicorn、12-factor、CI/CD、Kubernetes、可觀測性 |
| 20 | 安全與系統設計面試 `20-security-system-design` | 輸入驗證、注入、認證授權、JWT、密鑰、OWASP、系統設計案例、Python 面試題庫 |
| 21 | 微服務 `21-microservices` | gRPC、protobuf、服務發現、API gateway、健康檢查、限流與熔斷 |
| 22 | 分散式系統 `22-distributed-systems` | CAP、一致性、分散式鎖、訊息佇列、冪等、Saga、分散式追蹤 |

> **缺口修訂（2026-07-02）**：初版規劃 20 Part / 178 章。經章節缺口盤點後補強為 **22 Part / 241 章**：
> 於既有 Part 末尾追加重要主題（Enum、metaclass、walrus、EAFP/LBYL、ExceptionGroup、
> 現代 typing PEP 695、asyncio TaskGroup、argparse、pickle、decimal、HTTP client、
> FastAPI Depends、async DB / N+1、DDD/Hexagonal 等），並新增 Part 21 微服務、Part 22 分散式系統。
> 追加一律接在各 Part 末尾、既有章節編號不動，以維持 Part 1 內文既有的前向連結有效。

### Part 1「入門 Getting Started」章節規劃（本次完整交付）

| 章 | 檔名 | 主題 |
|----|------|------|
| 01 | `01-why-python.md` | 為什麼是 Python：設計哲學、應用領域、直譯式與動態型別 |
| 02 | `02-install-and-interpreter.md` | 安裝 Python、CPython 與其他實作、版本管理 |
| 03 | `03-repl-and-first-program.md` | REPL、第一支程式、`python` 指令、`__main__` |
| 04 | `04-pip-and-packages.md` | pip、PyPI、安裝與管理套件 |
| 05 | `05-venv.md` | 虛擬環境 venv：為什麼需要、如何使用 |
| 06 | `06-modules-and-import.md` | module、import 系統、`sys.path` |
| 07 | `07-packages-and-init.md` | package、`__init__.py`、相對/絕對 import |
| 08 | `08-pep8-and-style.md` | PEP 8、命名慣例、Pythonic 風格 |
| 09 | `09-project-layout.md` | 專案結構、`src` layout、`pyproject.toml` 入門 |
| 10 | `10-python2-vs-3.md` | Python 2 vs 3、版本演進與 `__future__` |
| 11 | `11-editor-and-tooling-setup.md` | 編輯器設定、type checker、linter、formatter 入門 |
| 12 | `12-how-python-runs.md` | Python 如何執行：source → bytecode → PVM（承接第 10 Part） |

---

## Acceptance Criteria（驗收標準）

本次交付（骨架 + Part 1）視為完成需滿足：

- [ ] 頂層 `README.md` 存在，含定位、20 Part 章節表、Repository 結構、使用方式
- [ ] `CLAUDE.md` 存在，定義內容型專案規範（章節模板、命名、語言、commit、Python 程式碼規範）
- [ ] `pyproject.toml`、`Makefile`、`Dockerfile`、`.github/workflows/ci.yml`、`.gitignore` 存在且內容合理
- [ ] `chapters/` 下 20 個 Part 資料夾全部建立，每個含 `README.md` 索引（列出該 Part 章節規劃）
- [ ] Part 1 的 12 章 `.md` 全部寫完，符合章節模板，章與章以「下一章」串接
- [ ] Part 1 的可執行範例（如有）置於 `examples/`，`pytest` 通過；`ruff`/`mypy` 無誤（若已安裝）
- [ ] `examples/`、`exercises/`、`solutions/`、`interview/`、`project/` 目錄骨架存在（含 README 佔位）

## Edge Cases（邊界情況）

- 使用者環境未安裝 Python / 未安裝開發工具：範例仍須「可讀、正確」，驗證步驟標為選用。
- Windows 環境：指令範例需同時考量 PowerShell / cmd（venv 啟用路徑不同）。
- 章節間交叉引用：連結須使用相對路徑，避免死連結。

## Data Model / State（不適用）

內容型專案，無資料模型與狀態機。實戰 `project/`（FastAPI task-api）之資料模型在該 Part 實作時另訂。

## Non-Functional Requirements（非功能需求）

- **可驗證性**：範例可 `pytest` 執行；程式碼經 `ruff` / `mypy`。
- **正確性**：涉及 CPython 底層（引用計數、GC、GIL、bytecode）須正確且可查證，必要時標註 Python 版本（預設 3.12+）。
- **一致性**：全書章節模板一致、命名一致、繁中說明 + 英文技術名詞。
- **可維護性**：每 Part 獨立索引、章節可依序閱讀。

## 命名規則

- Part 資料夾：`NN-<topic>`（兩位數 + kebab-case）。
- 章節檔：`NN-<kebab-case>.md`，編號於該 Part 內由 01 起算。
- 每個 Part 資料夾內須有 `README.md` 索引。

## Commit 規範（沿用全域）

```text
[feature][type][scope] description

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

- `feature`：Part 或主題（如 `getting-started`、`concurrency`）。
- `type`：`feat` / `fix` / `docs` / `chore` / `refactor`。
- 僅在使用者明確要求時才 commit / push。

## 交付範圍與後續

- **本次**：repo 骨架 + Part 1（12 章）完整內容。
- **後續**：逐 Part 補完 Part 2–20；實戰 `project/`（FastAPI task-api）於 Part 14 前後實作。
