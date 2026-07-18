# CLAUDE.md — Python Handbook 專案規範

本檔案提供給在此 Repository 協作的 AI（Claude Code 等）。
請在進行任何 Write / Edit 之前先閱讀本檔，並遵循以下規範。

---

## 專案性質

這是一本 **Python 學習手冊**，目標是帶讀者從**完全沒接觸過 Python** 一路到 **Senior / Python 架構師**。

- 內容主體是 **Markdown 章節**（`.md`），不是應用程式。
- 章節中的程式碼以 **Python** 為主，且應可實際執行。
- 設計理念為「由底層往上」：先理解語言模型 / CPython 執行機制，再往上學框架與架構。
- 採 **Python 原生改編**：章節模板骨架源自 golang-handbook，但將 Go 專屬主題
  （goroutine/channel、GMP、runtime GC）替換為 Python 對應主題（GIL/asyncio、CPython 內部與引用計數 GC）。
- 參考結構源自 `newman0934/golang-handbook`。
- **全書共 31 個 Part**（388 章），分兩條主線：
  - **Python 工程主線（Part 1–22）**：語言核心 → 並發 → CPython 內部 → 標準庫/測試/打包 → Web/資料庫 → 架構 → 微服務/分散式。
  - **資料 / AI / 部署主線（Part 23–31）**：資料分析 → 統計 → 機器學習 → 深度學習 → LLM/RAG/Agent → 生產化 AI → 雲端平台部署。

> 因為這是**內容型（documentation）** 專案，全域 CLAUDE.md 的 SDD/PRD 程式碼開發流程
> 不直接套用於「章節撰寫」。章節改以本檔定義的**章節模板**為準；
> 但 commit 規範、語言規範仍須遵循。

---

## 語言規範

- 預設語言為 **繁體中文（zh-TW）**。
- 以下維持英文：程式碼、套件/型別/函式名稱、API 路徑、技術專有名詞（GIL、asyncio、decorator、generator…）、commit 格式。
- 說明、教學、註解（非程式碼）一律使用繁體中文。
- **專有名詞雙語對照（首次出現時務必成對）**：
  - 中文名詞旁附英文：如「引用計數（reference counting）」「垃圾回收（garbage collection）」。
  - 英文名詞旁附中文：如「decorator（裝飾器）」「generator（產生器）」「context manager（情境管理器）」。
  - 只在**該章首次出現**時標；之後沿用即可，不必每次都附，以免干擾閱讀。

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
├── docs/                           # 設計文件與 spec（docs/superpowers/）
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

## 💡 白話導讀（建議先讀）      ← 必備，全書所有章節皆有
## 🎯 什麼時候會用到            ← 選用（抽象/理論章建議加）
## 🔗 前端對照（選用）          ← 有 JS/TS 平行概念時才加
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

- **`💡 白話導讀`（必備）**：擺在開頭引言之後、`Why` 之前。用**生活比喻**把觀念講白，
  讓「第一次接觸的讀者」也能懂；技術名詞**後置**（先講白話，再貼上術語標籤）。詳見「可讀性原則」。
- **`🎯 什麼時候會用到`（選用）**：擺在導讀之後、`Why` 之前。用於**抽象／理論章**
  （如 descriptor、metaclass、Protocol、weakref、generator）——這類章「機制講得清楚，但讀者不知何時該用」。
  內容要**點名真實工具／框架 + 具體情境 + 決策訊號**（例：descriptor → Django/SQLAlchemy 的欄位、驗證器）。
  方法／工具型章節（stdlib、資料結構等）若 `Best Practice` 已有「情境 → 用什麼」的決策清單，就不必重複加。
- **`🔗 前端對照`（選用）**：擺在導讀／🎯 之後、`Why` 之前。**只在 JS/TS 有明確平行概念、
  且對照真能加深理解時才加**（本書與姊妹作 `frontend-handbook` 共用讀者群，很多人一邊會、一邊在學）。
  用一個小表格或兩三句點出「**相同處 → 關鍵差異**」，例：`asyncio` ↔ JS event loop（都是單執行緒事件迴圈；
  差別：JS 只有 async、Python 還有 threading/multiprocessing）、type hints ↔ TS types（都是註記；
  差別：TS 編譯期擦除、Python 保留在 `__annotations__` 供 runtime 讀）、decorator ↔ JS/TS decorator、
  comprehension ↔ `map`/`filter`、closure ↔ JS closure（幾乎相同）。**沒有真平行概念的章節（如 GIL 細節、
  CPython 內部、後端/OS）就別硬湊**——寧缺勿湊。適合對照的多在語言核心（Part 1–9）與型別（Part 5）。
- 章節結尾以「下一章」串接，維持可依序閱讀的動線。
- 圖解使用 **Mermaid**（` ```mermaid `）。

### 統整章模板（每個 Part 的最後一章）

每個 Part 以一章 **`NN-summary.md`** 收尾，把該 Part 所有章節串成整體。
**它不套用上面的標準模板**（回顧章不需要 Why/Theory/Implementation），而是用以下結構：

```markdown
# Part N 統整：<主題>全貌

> 一句話：把這 N 章串成一張圖——你現在該具備什麼能力。

## 🗺️ 知識地圖（這 N 章怎麼串起來）   ← 必備，含 Mermaid
## ⚡ 速查表（什麼情境用什麼）           ← 必備，表格 + 章節連結
## 🔑 核心心智模型（帶得走的幾句話）     ← 本 Part 的比喻／世界觀總結
## 🛠️ 小實作（用上這一 Part 的東西）    ← 必備，可執行範例 + 預期輸出
## ✅ 自測清單（答不出來就回去讀）       ← 必備，每項附章節連結
## 🎯 面試速查                          ← 必備

---

➡️ 下一 Part：[...](../NN-next/README.md)

[⬆️ 回 Part N 索引](README.md)
```

- **例外**：Part 23–27、29–31 已有 `NN-capstone-*.md`（整合**實作**專案），性質等同統整章，不另加。
- `scripts/check_chapters.py` 會依檔名 `-summary.md` 自動套用這組必備區塊。

---

## 程式碼規範

- 範例使用 **idiomatic / Pythonic** 寫法，能實際 `python` 執行、`pytest` 通過。
- 基準版本：**Python 3.12+**（如用到特定版本特性，於該處標註）。
- 通過 **ruff**（lint + format）與 **mypy**（型別檢查）。
- 需要驗證行為的範例放進 `examples/`，並附 `test_*.py`（優先參數化測試 `pytest.mark.parametrize`）。
- **程式碼區塊的 fence 約定（重要，勿混用）**：
  - ` ```python ` = **必須是可實際執行的 Python**。日後的自動檢查只掃這種區塊，
    放進不可執行的東西會讓檢查失效（曾發生 f-string 大括號跳脫錯誤未被發現）。
  - ` ```pycon ` = REPL 互動示範／預期輸出。
  - ` ```text ` = **語法示意、虛擬碼、非 Python 的指令**（如 `name := expression`、
    IPython 魔術指令 `%timeit`、示意用的 SQL/流程圖），並在下方標註「不可直接執行」。
  - ` ```bash ` / ` ```sql ` / ` ```dockerfile ` 等 = 對應語言的真實指令。
- 錯誤處理示範採 Python 慣例（明確 `except` 型別、`raise ... from`、context manager），避免裸 `except:`。

---

## 內容品質要求

**核心原則一：寧可詳盡，不要簡略。** 本書目標是「讀完就懂到能面試、能實戰」，
因此每章必須把觀念**講透**，而非點到為止。寫作深度以「讀者第一次接觸也能完全看懂」為準。

**核心原則二：詳盡 ≠ 密集。** 「詳盡」是指**把脈絡補足**，不是把資訊壓縮成高密度的段落。
兩者衝突時，**以讀者能否讀懂為準**。

### 可讀性原則（實際回饋後確立，務必遵守）

早期章節雖然「詳盡」，卻寫成了**百科式的密集段落**——一句話塞進多個新術語、通篇粗體、
沒有比喻、沒有緩坡——結果讀者反映「看不懂」。因此確立以下寫作規範：

- **先白話，後術語**：先用日常語言把概念講清楚，**再貼上技術名詞當標籤**
  （❌「閉包是捕獲了自由變數的詞法環境」→ ✅「這個函式記得它出生時身邊的變數——這叫閉包」）。
- **寫成流暢敘事，不要碎片**：一個完整想法用**完整句子**講完，把「因為 → 所以」「不是 A 而是 B」
  的連接詞寫出來；不要把一句話剁成六七行、也不要通篇 `>` 引言讓讀者自己拼。
- **善用生活比喻，且跨章沿用**：抽象機制一律配一個具體比喻，並**跨章沿用同一套**，建立一致的世界觀。
  新增比喻請盡量沿用下表、不要每章換一套；下表為維護中的清單（見「跨章比喻表」）。
- **一句一個概念**：句子短。不要把三個新觀念塞進同一句。
- **從零鋪陳前置知識**：不要假設讀者已懂前提。若一章需要某個前置概念
  （如 argparse 需要先懂「命令列參數」是什麼），**就在該章從零講起**，別直接跳進主題。
- **粗體要節制**：滿版粗體等於沒有重點。
- 對「讀者可能問的笨問題」要正面回答，不要跳過。

> 檢驗標準：**一個第一次接觸這個主題的人，能不能靠這章自己讀懂？**
> 若答案是否定的，再詳盡也是失敗的。

#### 把解說寫得更有戲（讓讀者「被說服」，不只「被告知」）

「讀得懂」還不夠，要讓讀者**想讀下去、記得住**。以下六個手法（源自對照姊妹作 `nest-handbook` 後歸納，
證實能明顯提升清晰感），**尤其用在 `💡 白話導讀` 與 `🎯`**——別把章節寫成「資訊密度高但沒有溫度的參考書」：

1. **驅動問題 + 重新框定**：把枯燥主題重寫成一個勾人的問題，並和「課本結論」劃清界線。
   （✅「這章真正要講的，不是『TCP 比較可靠』這種課本結論——**是那三次握手要花多少錢**。」）
2. **講清楚「不懂會怎樣」的代價**：把痛講到讓人有感，不要只講好處。
   （✅「不做連線重用，跨區呼叫就是『服務能用』與『服務不能用』的差異。」）
3. **預告證據與數字（懸念）**：章內有可執行範例時，**在開頭就用結果勾住讀者**。
   （✅「這章會**真的量給你看**——劇透：同樣的請求，270ms → 95ms。」）本書每章都有可跑的範例，善用這個優勢。
4. **超具體的 `🎯`**：列**可辨識的真實時刻**（含「面試被問到 X」「你收到某個錯誤想查」），而非抽象情境分類。
   （✅「你收到 `Too many open files`，想知道誰把 fd 用光了。」）
5. **修辭節奏**：關鍵處穿插**極短的獨立句**製造重音（「**它不是。**」）——這是節奏，不是「碎片化」（碎片化是把一個完整想法剁成多行）。
6. **跨章比喻回呼**：沿用[跨章比喻表](#跨章比喻表建立一致世界觀新增請沿用)時，明確「回到某章那個比喻」接續，讓世界觀長出來。
   （✅「還記得 [ch02] 的取餐號碼牌嗎？連線池就是櫃檯先抽好一排號碼牌等你用。」）

> 分寸：這是「加戲」不是「灌水」。戲要短、要準、要服務理解；一個比喻演一次就好，別把「純粹是廢話」講三遍。

#### 跨章比喻表（建立一致世界觀，新增請沿用）

| 概念 | 比喻 |
|------|------|
| GIL | 餐廳只有一把菜刀：同一時刻只有一個執行緒能真正動手 |
| asyncio / event loop | 單人服務生：不呆等，一桌在等就先去招呼下一桌 |
| 快取 cache | 櫃檯便條：算過的答案貼起來，下次直接看，不重算 |
| 變數 / 名稱綁定 | 變數不是盒子，是**標籤**——貼在物件上，可多張標籤貼同一個物件 |
| 檔案描述符 fd | 取餐號碼牌：檔案、socket、pipe 都領一個號碼，OS 只認號碼 |
| 冪等 idempotency | 取件編號：拿同一張編號問幾次，只會拿到那一件（做多次＝做一次）|
| RAG | 開書考試：先翻資料、再作答 |

（新增比喻請優先沿用上表；真的要新增，就補進這張表，別讓同一概念在不同章有不同比喻。）

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
4. **接好導覽後跑 `python scripts/gen_nav.py --fix`**（或 `make nav`）：它會自動修正
   `chapters/README.md` 與本檔的章數，並檢查「下一章 / 下一 Part」連結、Part README
   是否列齊該 Part 每一章。CI 也會跑 `gen_nav.py`（檢查模式），連結接錯會擋下。
   （注意：本工具**只自動改章數**，footer/README 的內容與標點不會被它重寫，需手動維護。）
5. 驗證通過後再回報完成，不得在未驗證下宣稱完成。
