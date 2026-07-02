# CLAUDE.md — Python Handbook 專案規範

本檔案提供給在此 Repository 協作的 AI（Claude Code 等）。
請在進行任何 Write / Edit 之前先閱讀本檔，並遵循以下規範。

---

## 專案性質

這是一本 **Python 學習手冊**，目標是帶讀者從**完全沒接觸過 Python** 一路到 **Senior / Python 架構師**。

- 內容主體是 **Markdown 章節**（`.md`），不是應用程式。
- 章節中的程式碼以 **Python** 為主，且應可實際執行。
- 設計理念為「由底層往上」：先理解語言模型 / CPython 執行機制，再往上學框架與架構。
- 採 **Python 原生改編**：保留 golang-handbook 的 20 Part 骨架與章節模板，但將 Go 專屬主題
  （goroutine/channel、GMP、runtime GC）替換為 Python 對應主題（GIL/asyncio、CPython 內部與引用計數 GC）。
- 參考結構源自 `newman0934/golang-handbook`。

> 因為這是**內容型（documentation）** 專案，全域 CLAUDE.md 的 SDD/PRD 程式碼開發流程
> 不直接套用於「章節撰寫」。章節改以本檔定義的**章節模板**為準；
> 但 commit 規範、語言規範仍須遵循。

---

## 語言規範

- 預設語言為 **繁體中文（zh-TW）**。
- 以下維持英文：程式碼、套件/型別/函式名稱、API 路徑、技術專有名詞（GIL、asyncio、decorator、generator…）、commit 格式。
- 說明、教學、註解（非程式碼）一律使用繁體中文。

---

## 目錄結構

```text
python-handbook/
├── README.md
├── CLAUDE.md
├── pyproject.toml                  # 專案設定與依賴（examples/exercises/solutions/project 共用）
├── Makefile                        # 常用指令入口（make test / lint / run / docker-build）
├── Dockerfile                      # 實戰專案打包
├── .github/workflows/              # CI：ruff + mypy + pytest
├── chapters/
│   └── NN-<topic>/                 # 例：09-concurrency/
│       ├── README.md               # 該 Part 的章節索引
│       └── NN-<kebab-case>.md      # 例：05-asyncio.md
├── examples/                       # 可執行範例（pytest 驗證）
├── exercises/                      # 練習題（stub + 測試，實作前為紅燈）
├── solutions/                      # 練習解答（全綠）
├── interview/                      # Python 面試題庫
└── project/                        # 貫穿全書的實戰專案：task-api（FastAPI 分層服務）
```

### 命名規則

- Part 資料夾：`NN-<topic>`（兩位數編號 + kebab-case），如 `03-data-structures`。
- 章節檔：`NN-<kebab-case>.md`，如 `05-venv.md`，編號於該 Part 內由 01 起算。
- 每個 Part 資料夾內須有 `README.md` 作為章節索引（列出該 Part 所有章節連結）。

---

## 章節模板

每一章 `.md` 內容**至少**涵蓋以下區塊（依需要增減，但順序固定）：

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

- 章節結尾以「下一章」串接，維持可依序閱讀的動線。
- 圖解使用 **Mermaid**（` ```mermaid `）。

---

## 程式碼規範

- 範例使用 **idiomatic / Pythonic** 寫法，能實際 `python` 執行、`pytest` 通過。
- 基準版本：**Python 3.12+**（如用到特定版本特性，於該處標註）。
- 通過 **ruff**（lint + format）與 **mypy**（型別檢查）。
- 需要驗證行為的範例放進 `examples/`，並附 `test_*.py`（優先參數化測試 `pytest.mark.parametrize`）。
- 章節內嵌的程式碼片段標註語言：` ```python `；REPL 互動示範可用 ` ```pycon `。
- 錯誤處理示範採 Python 慣例（明確 `except` 型別、`raise ... from`、context manager），避免裸 `except:`。

---

## 內容品質要求

**核心原則：寧可詳盡，不要簡略。** 本書目標是「讀完就懂到能面試、能實戰」，
因此每章必須把觀念**講透**，而非點到為止。寫作深度以「讀者第一次接觸也能完全看懂」為準。

### 深度要求（每章適用）

- 解釋「**為什麼這樣設計**」，不只是「怎麼用」。要交代來龍去脈、設計動機、與其他做法的取捨。
- **每個區塊都要展開說明**，不只列重點：
  - `Why`：說清楚沒有這個特性會遇到什麼問題、它解決了什麼痛點。
  - `Theory`：完整鋪陳觀念，必要時從更基礎的前提講起，逐步推導。
  - `Specification`：語法/語意規則要完整列舉，含例外與特殊情況。
  - `Implementation`：講到 CPython 實際如何運作（物件模型、引用計數、bytecode 等），
    可用 `dis`、`sys.getrefcount`、`id()` 等佐證。
  - `Code Example`：提供**多個**由淺入深的範例，每個範例都要有**逐行或分段的文字解說**，
    並示範「正確 vs 錯誤」對照。範例須可實際執行、輸出可預期（附預期輸出）。
  - `Common Mistakes`：列出多個真實會踩的坑，說明**為什麼會錯、錯了會怎樣、如何修正**。
  - `Interview Notes`：不只列考點，要寫出「面試官想聽到的完整回答」。
- 涉及底層（引用計數、GC、GIL、bytecode、記憶體管理）需正確且可查證，必要時標註 Python 版本，
  並盡量用可執行程式碼驗證論點（如用 `dis.dis`、`gc`、`sys` 模組實測）。
- 技術名詞首次出現給中文說明 + 英文原文。
- 適時以表格、Mermaid 圖、對照範例輔助理解；長主題可加「延伸」「補充」小節。
- 交叉引用相關章節（用相對連結），建立知識網絡。
- 不抄襲；範例自行撰寫並驗證。

### 篇幅參考

- 一般章節：內容應充分展開，不因「看似簡單」而草草帶過；簡單主題也要補足脈絡、範例與陷阱。
- 核心/困難主題（GIL、asyncio、GC、MRO、decorator、descriptor 等）：需更長篇幅，
  多圖多例、逐步拆解，直到讀者能自行解釋原理。

---

## Commit 規範

格式（沿用全域規範）：

```text
[feature][type][scope] description
```

- `feature`：所屬 Part 或主題，如 `getting-started`、`concurrency`、`web`。
- `type`：`feat` / `fix` / `docs` / `chore` / `refactor`。
- `scope`：細部範圍，如 `chapter`、`example`、`readme`。

範例：

```text
[getting-started][docs][chapter] 新增 venv 章節

[concurrency][docs][chapter] 補充 GIL 與 asyncio 圖解

[examples][feat][concurrency] 新增 asyncio 併發下載可執行範例
```

所有 commit 必須包含：

```text
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

> 僅在使用者明確要求時才建立 commit 或 push。

---

## 工作流程建議

1. 撰寫/修改章節前，先看該 Part 的 `README.md` 索引，確認章節編號與定位。
2. 完成章節後：更新該 Part `README.md` 索引、串好上一章/下一章連結。
3. 有可執行範例時：放入 `examples/`，跑 `pytest`、`ruff check .`、`mypy`。
4. 驗證通過後再回報完成，不得在未驗證下宣稱完成。
