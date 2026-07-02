# 編輯器與工具鏈設定

> 一個現代 Python 開發環境 = 編輯器 + linter + formatter + type checker + test runner；把這套配起來，機器會在你出錯的當下就告訴你，而不是等到執行時才炸。

## Why（為什麼）

Python 是動態語言——很多錯誤（拼錯變數名、型別不對、忘了 import）在「執行到那一行」之前不會被發現。這在小腳本無所謂，在大專案卻是災難：一個藏在少走的分支裡的 typo，可能上線後才爆。

解法是把一套**工具鏈**接進編輯器，讓它們在你**打字的當下**就靜態分析程式、標出問題。這等於把「執行期才會遇到的錯」提前到「編輯期」。配好這套環境，是從「會寫 Python」邁向「專業寫 Python」的分水嶺。

## Theory（理論：現代 Python 工具鏈的四個角色）

一套完整工具鏈由四類工具組成，各司其職：

| 角色 | 做什麼 | 代表工具 |
|------|--------|----------|
| **Linter** | 抓可疑寫法、未用變數、潛在 bug、風格問題 | **ruff**、flake8、pylint |
| **Formatter** | 自動排版（縮排、空格、換行），統一風格 | **ruff format**、black |
| **Type checker** | 依型別註記做靜態型別檢查 | **mypy**、pyright |
| **Test runner** | 執行測試、報告結果與覆蓋率 | **pytest** |

現代趨勢是 **ruff** 一個工具同時扮演 linter + formatter（用 Rust 寫成，比舊工具快數十倍），大幅簡化配置。

編輯器（VS Code、PyCharm 等）的角色是**把這些工具整合進來**：透過 **LSP（Language Server Protocol）** 這個標準協定，編輯器與語言伺服器（如 Pylance / pyright）溝通，即時提供補全、跳轉定義、錯誤標示。

## Specification（規範：安裝與設定）

### 安裝工具（裝進虛擬環境）

```bash
python -m pip install ruff mypy pytest
```

### 集中設定在 `pyproject.toml`

所有工具的設定放同一個檔，團隊與 CI 共用一套標準：

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]   # 錯誤/警告類別：pycodestyle, pyflakes, isort, pyupgrade, bugbear

[tool.mypy]
python_version = "3.12"
strict = true                          # 開啟嚴格型別檢查

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### 常用指令

```bash
ruff check .           # lint 檢查
ruff check --fix .     # lint 並自動修可修的
ruff format .          # 自動排版
mypy .                 # 型別檢查
pytest                 # 跑測試
```

## Implementation（編輯器整合與運作方式）

### VS Code（最常見）

裝三個擴充套件即可組成完整環境：

- **Python**（Microsoft）：基礎支援、選直譯器、跑/除錯。
- **Pylance**：型別感知的智慧補全與即時錯誤（基於 pyright）。
- **Ruff**：即時 lint 與存檔自動格式化。

`.vscode/settings.json` 建議：

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  }
}
```

**最關鍵的一步：讓編輯器選到你虛擬環境的直譯器**（`.venv/bin/python`）。否則編輯器用的是別的 Python，補全與檢查都會對不上你真正的環境——這是新手「編輯器一直報 import 錯，但程式明明能跑」的頭號原因。

### 運作方式：存檔即修正

配好之後的日常體驗：

1. 打字時，Pylance 即時標紅「未定義的變數」「型別不符」。
2. 存檔的瞬間，ruff 自動排版 + 排序 import + 修掉可自動修的問題。
3. commit 前，`mypy` 與 `pytest` 把關（可用 pre-commit 自動化，見 [pre-commit](../13-tooling-packaging/08-pre-commit.md)）。

錯誤被層層提前：**編輯期（Pylance）→ 存檔（ruff）→ commit（pre-commit）→ CI**。越早抓到的錯越便宜。

## Code Example（工具如何抓出你看不到的錯）

以下這段程式**語法完全正確、能通過直譯器載入**，但藏著三個問題：

```python
# buggy.py
import os          # 未使用的 import


def calc(x):       # 缺型別註記
    total = x + 1
    return totl    # 拼錯：totl 應為 total（NameError，但只在執行到時才炸）
```

工具能在**不執行**它的情況下抓出來：

```pycon
$ ruff check buggy.py
buggy.py:2:8: F401 [*] `os` imported but unused
buggy.py:7:12: F821 Undefined name `totl`
Found 2 errors.

$ mypy buggy.py
buggy.py:5: error: Function is missing a type annotation  [no-untyped-def]
```

解說：

- `F401` 抓到沒用到的 `import os`。
- `F821` 抓到 `totl` 這個**拼錯的變數名**——這在動態語言裡原本要「執行到那一行」才會 `NameError`，ruff 讓你在打字當下就看到。
- mypy 提醒 `calc` 缺型別註記（strict 模式）。

這正是工具鏈的價值：**把執行期才會爆的錯，提前到編輯期。**

## Diagram（圖解：錯誤被提前攔截的層層防線）

```mermaid
flowchart LR
    A[打字] -->|Pylance 即時| B[存檔]
    B -->|ruff format + fix| C[commit]
    C -->|pre-commit: mypy/pytest| D[push]
    D -->|CI: ruff/mypy/pytest| E[合併]
    style A fill:#e8f5e9
    style E fill:#e3f2fd
```

> 越靠左（越早）攔到的錯，修起來越便宜。

## Best Practice（最佳實踐）

- **編輯器一定選到 `.venv` 的直譯器**：這是讓補全/檢查正確的前提，也是最常被忽略的一步。
- **用 ruff 一次搞定 lint + format**：比 flake8 + black + isort 的組合更快、更好配。
- **開 formatOnSave**：讓排版變成無意識的自動行為，別再手動對齊。
- **型別檢查從寬到嚴**：舊專案可先不 strict，新專案直接 `strict = true`，逼自己寫好註記（見 [Part 5](../05-typing/README.md)）。
- **設定集中在 `pyproject.toml`**：一份設定，編輯器、CLI、CI 共用，避免「本地過、CI 掛」。
- **用 pre-commit 把關**：commit 前自動跑 ruff/mypy，擋下不合格的提交（見 [pre-commit](../13-tooling-packaging/08-pre-commit.md)）。

## Common Mistakes（常見誤解）

- **編輯器選錯直譯器**：報一堆 import / 型別錯，但程式在終端機能跑——因為編輯器用的不是你的 `.venv`。先檢查右下角/狀態列的直譯器路徑。
- **本地沒裝工具卻期待編輯器會檢查**：ruff/mypy 要**裝進環境**，擴充套件才叫得動它們。
- **本地與 CI 用不同設定**：導致「本地綠、CI 紅」。把設定統一放 `pyproject.toml`。
- **把 formatter 和 linter 的職責搞混**：formatter 只管排版（不改邏輯），linter 抓可疑寫法與 bug；兩者互補。
- **關掉所有警告圖個清靜**：警告是免費的 bug 預警，該修不是該關。
- **以為 type checker 會在執行時檢查型別**：mypy 是**靜態**檢查（不執行程式）；型別註記在執行期預設不強制（見 [Part 5](../05-typing/01-why-type-hints.md)）。

## Interview Notes（面試重點）

- 說得出現代 Python 工具鏈的**四個角色**：linter、formatter、type checker、test runner，並點名代表工具（ruff / mypy / pytest）。
- 知道 **ruff 同時做 lint + format**、以速度著稱，是目前主流。
- 理解工具鏈的價值：**把動態語言的執行期錯誤提前到編輯/靜態檢查期**（如拼錯變數名、未用 import、型別不符）。
- 知道編輯器透過 **LSP** 整合語言伺服器（Pylance/pyright），且**選對虛擬環境直譯器**是關鍵。
- 知道設定集中在 `pyproject.toml`、並可用 pre-commit / CI 層層把關。
- 知道 **mypy 是靜態檢查、不在執行期強制型別**。

---

➡️ 下一章：[Python 如何執行：source → bytecode → PVM](12-how-python-runs.md)

[⬆️ 回 Part 1 索引](README.md)
