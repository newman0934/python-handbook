# Python Engineering Handbook — 增補設計（Amendment Spec）

> 日期：2026-07-14
> 狀態：待使用者審閱
> 對象：**已完成**的 python-handbook（31 Part、368 章，全數通過 CI）
> 前置文件：`2026-07-02-python-handbook-design.md`（原始設計，描述已建成的書）

---

## 動機

本書已完成並自洽。這份增補**不是修 bug，而是完整性補強**——來源是與姊妹書
`nest-handbook` 的 design 逐一對照後浮現的缺口。

對照照出一個**鏡像盲點**：

> **python-handbook 深深往「語言底層」鑽**（Part 10 整個講 GIL、引用計數、bytecode），
> **卻幾乎不往「機器 / 網路底層」鑽**。實查證實：全書**沒有** OSI/TCP/三次握手/TLS 握手的
> 專門章；`SIGTERM`/`SIGKILL` 用了（Part 19 優雅關閉）卻從沒把「作業系統訊號」從頭教過；
> 沒有 Linux/process/檔案描述符 的基礎。
>
> 反觀 nest-handbook 刻意用 Part 1–3（網路/HTTP/HTTPS、Linux/OS）補了這一層。
> 兩本書是鏡像盲點：python 語言深、網路 OS 淺；nest 補了網路 OS、語言內部（V8）較淺。

對「從零到 Senior / 架構師」的定位而言，網路 + OS 這一層是真實盲點。

---

## 設計原則（針對「已完成的書」）

1. **能折疊當章，就別新增 Part。** 本書已有 368 章、大量相對連結與導覽鏈；
   在中間插入新 Part 會**連鎖重編號**（Part 23–31 全要改資料夾名 + 內部連結），成本極高。
2. **前置內容用 `Part 0`（`00-` 前綴）。** 排序自然落在 `01-` 之前，
   **完全不動任何現有 Part 的編號**——這是加「網路/OS 基礎」而不重編號的關鍵手法。
3. **沿用既有規範。** 白話導讀（必備）、🎯 使用場景（抽象章）、`NN-summary.md` 統整章、
   `scripts/check_chapters.py`、`examples/exercises/solutions`、fence 約定，全部照舊。
4. **抵抗範圍膨脹。** 明確記錄「刻意不做」的項目，避免無限擴張（見末段）。

---

## 現況基準

- **31 Part、368 章**；工程主線 Part 1–22、資料/AI 主線 Part 23–31。
- 既有工具鏈：ruff / mypy / pytest / `check_chapters.py` 全綠。
- 章數一致性由 `check_chapters.py` 自動守門（CLAUDE.md 與 `chapters/README.md` 的數字不得過時）。

---

## 提案總表

| # | 提案 | 放置策略 | 需重編號？ | 優先 |
|---|------|----------|-----------|------|
| A | **Part 0：後端與網路/OS 基礎**（新增） | `chapters/00-backend-foundations/`（`00-` 前綴，排在 Part 1 前） | ❌ 否 | ★★★ |
| B | **背景任務進階：Celery / 任務佇列 / 排程** | 折疊進 **Part 14 Web**（接在 ch12 `async-web-background` 之後） | ❌ 否 | ★★★ |
| C | **作為可靠的 HTTP 客戶端**（對外整合視角） | 折疊進 **Part 21 微服務** | ❌ 否 | ★★ |
| D | **API 契約設計深化**（RFC 9457 / ETag / webhook HMAC） | 折疊進 **Part 14 Web** | ❌ 否 | ★★ |

**四項全部零重編號**：A 用 `00-` 前綴、B/C/D 折疊進現有 Part。

---

## 提案 A：Part 0 — 後端與網路/OS 基礎（唯一新增 Part）

### 為什麼

本書假設讀者已懂網路與作業系統，於是全書「用而不教」——
連線池講 keep-alive、優雅關閉送 `SIGTERM`、資料庫連 TCP，卻沒有一處把這些底層講清楚。
對一本標榜「從零開始」的書，這是斷層。

### 放置

- 資料夾：`chapters/00-backend-foundations/`
- 因 `00-` 排序在 `01-getting-started` 之前，**不動任何現有 Part 編號、不動任何現有連結**。
- 定位為「**前置通識**」，讀者可選讀；但每章結尾扣回「這對你寫 Python 後端的影響」，不是計概教科書。

### 章節規劃（約 9 章 + 統整）

| 章 | 主題 | 扣回 Python 後端的影響 |
|----|------|------------------------|
| 01 | 後端在做什麼：一個請求的完整旅程 | Browser → DNS → TCP → TLS → WSGI/ASGI → DB → Response，串起全書地圖 |
| 02 | TCP / UDP 與可靠傳輸 | 三次握手 → 理解**連線池與 keep-alive**為何存在（呼應 Part 15） |
| 03 | DNS 與 IP / Port | 服務發現、`localhost` vs `0.0.0.0` 綁定、容器網路的前置 |
| 04 | HTTP 報文深入 | method / status / header / Cookie，補足 Part 14 之下的一層 |
| 05 | HTTPS 與 TLS | 對稱/非對稱加密、雜湊、數位簽章、憑證鏈、TLS 握手、HTTP/1.1 vs 2 vs 3 |
| 06 | Linux process 與 thread | fork/exec、程序模型 → 呼應 Part 9 GIL/multiprocessing 的世界觀 |
| 07 | 檔案描述符與 I/O | fd、stdin/stdout/管線、阻塞 vs 非阻塞 → 呼應 Part 9 asyncio、Part 11 io |
| 08 | 訊號與程序生命週期 | `SIGTERM`/`SIGKILL`/`SIGINT` → **正式補上 Part 19 優雅關閉的地基** |
| 09 | shell、環境變數、常用診斷 | `ps`/`top`/`lsof`/`netstat`、env → 呼應 12-factor 與雲原生 |
| 10 | **Part 0 統整** | 知識地圖 + 小實作（最小 TCP echo server / 用 `socket` 手打一個 HTTP 回應） |

> `examples/part00/`：以**可執行的診斷腳本**與**最小 socket server**呈現，不強求應用碼。

---

## 提案 B：Part 14 擴充 — 背景任務進階（Celery / 任務佇列 / 排程）

### 為什麼

實查：本書目前只有 **FastAPI 的 in-process `BackgroundTasks`**（Part 14 ch12），
**完全沒有 Celery**——而 Celery 是 Python 後端的業界標準**分散式任務佇列**。
nest-handbook 給了它整個 Part（33 BullMQ）。這是明確的 Python 專屬缺口。

### 放置

接在 Part 14 現有的 `12-async-web-background.md` 之後（自然延續：
「in-process 背景任務不夠用時 → 分散式任務佇列」）。**因為插在 Part 14 內部、不跨 Part，不需重編號。**

### 新增章（約 3 章）

| 主題 |
|------|
| in-process 背景任務的極限 → 為什麼需要獨立的任務佇列（可靠性、重啟不丟、worker 與 API 分離） |
| **Celery** 實戰：broker（Redis/RabbitMQ）、task、result backend、重試與冪等、worker 部署 |
| **排程**：cron 型任務（Celery beat / APScheduler）、與 Part 22 冪等/至少一次投遞的接點 |

> 備選方案：獨立成一個 append 的新 Part。優點是主題更醒目；缺點是讀序落在 AI 線之後，
> 且 `BackgroundTasks` 與 Celery 分兩處。**建議採「折疊進 Part 14」**，教學連續性最佳。

---

## 提案 C：Part 21 擴充 — 作為可靠的 HTTP 客戶端（對外整合）

### 為什麼

與 nest 相同的缺口：全書幾乎都從「**我是 server**」寫（收請求、驗證、回應），
但資深後端有一半時間在「**我是 client**」——可靠地呼叫第三方與內部服務。
`httpx`/`requests` 散在十幾章，卻沒有一塊講「怎麼串一個會逾時的第三方 API」。
（熔斷器/重試在 Part 21/22/30 都有，但是當「模式」講，不是當「對外整合」講。）

### 放置

折疊進 **Part 21 微服務**（已有 `07-rate-limit-circuit-breaker`，把「消費端視角」補齊最自然）。

### 新增章（約 2 章）

| 主題 |
|------|
| 作為 HTTP 客戶端的可靠整合：逾時預算、重試 + 指數退避 + 抖動、**消費端**熔斷、`httpx` timeout/連線池 |
| 呼叫別人時**帶冪等鍵**、`asyncio` 取消與 `AbortController` 對應、第三方 SDK/wrapper 設計、webhook 接收端驗證 |

---

## 提案 D：Part 14 擴充 — API 契約設計深化

### 為什麼

實查：`RFC 9457`（problem details）**0 檔**、`ETag` 只 1 檔。
Part 14 的 `18-api-design` 只輕帶「版本、分頁、錯誤格式」。契約設計是資深 API 工程的硬功夫。

### 放置

折疊進 **Part 14 Web**（`18-api-design` 章群）。

### 新增章（約 2 章）

| 主題 |
|------|
| **錯誤契約 RFC 9457**（`application/problem+json`）、統一錯誤格式、破壞性變更與版本策略 |
| **ETag 與條件請求**（`If-None-Match`/`If-Match`）、快取標頭策略、**webhook 設計**（HMAC 簽章、重送、冪等） |

---

## 沿用的品質與驗證規範

- 每個新章：白話導讀（必備）、抽象章加 🎯、章末導覽鏈、相對連結。
- Part 0 以 `10-summary.md`（或該 Part 末章）收尾，套統整章模板。
- 受影響 Part（14、21）的**統整章需同步更新**（知識地圖 / 速查表 / 自測 / 面試速查涵蓋新章）。
- 有可執行行為的範例進 `examples/partNN/`，附 `test_*.py`；`exercises/solutions` 對應。
- `scripts/check_chapters.py` 需通過：新增的 `python` 區塊語法合法、統整章涵蓋該 Part 每一章、
  CLAUDE.md 與 `chapters/README.md` 章數一致（會自動抓 Part 0）。

---

## Acceptance Criteria

- [ ] `chapters/00-backend-foundations/` 建立，含 `README.md` 索引與約 10 章（含統整章）。
- [ ] Part 14 新增背景任務進階（B）與 API 契約深化（D）章群，統整章同步更新。
- [ ] Part 21 新增「作為可靠 HTTP 客戶端」章群（C），統整章同步更新。
- [ ] `chapters/README.md` 總覽新增 Part 0 列；CLAUDE.md 章數更新。
- [ ] `ruff` / `mypy` / `pytest`（project/examples/solutions）/ `check_chapters.py` 全綠。
- [ ] 每個新增可執行範例都實測過、附預期輸出（不得只是死程式碼）。

---

## 刻意不做（抵抗膨脹）

記錄此決策以防未來無限擴張：

| 想加的 | 為什麼不 |
|---|---|
| **Django 整個 Part** | 本書選了 FastAPI（如 nest 選 Nest）——這是框架選型，不是缺口。最多一章「Django vs FastAPI 選型對照」折疊進 Part 14 |
| 資料工程（Airflow / Spark / dbt） | 那是資料工程，不是 Python 後端（與既有 AI 線的邊界一致） |
| gRPC / protobuf 獨立成 Part | Part 21 微服務裡夠了 |
| 再擴 AI 線（Part 23–31） | 已有 9 個 Part、夠廣 |
| 網路/OS 拆成 3 個 Part（如 nest） | 本書定位是 Python 語言書；用**一個 Part 0** 濃縮即可，且每章必扣回「對寫後端的影響」，不寫成計概 |

---

## 放置與重編號決策（風險）

- **核心約束：不對現有 Part 重編號。** 手法：Part 0 用 `00-` 前綴；B/C/D 全折疊進現有 Part 內部。
  → 現有 368 章的資料夾名與相對連結**一律不動**。
- **Part 0 的定位風險**：容易寫成「計算機概論教科書」。護欄：**每章結尾都要有一段
  「這對你寫 Python 後端有什麼影響」**，且範例扣回 Python（`socket`、`signal`、`os`）。
- **統整章漏更新風險**：`check_chapters.py` 的「統整章必須涵蓋該 Part 每一章」檢查會自動攔截。

---

## 下一步

若採納，進入 writing-plans 產出 plan.md / tasks.md；建議交付順序：
**Part 0（A）→ Part 14 折疊（B、D）→ Part 21 折疊（C）**，每階段結束 CI 需全綠。
