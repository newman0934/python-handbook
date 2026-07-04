# Part 13 面試題:工程化與打包

> 對應 [Part 13 工程化與打包](../chapters/13-tooling-packaging/README.md)。核心:可重現性、pyproject.toml、打包、ruff/mypy/pre-commit 工具鏈。

---

## Q1. 怎麼保證環境可重現?app 和 library 釘版本的策略一樣嗎?

**考點**:可重現性([01-pip-deep](../chapters/13-tooling-packaging/01-pip-deep.md))

**答**:關鍵是**分離「宣告」與「鎖定」**:

- **宣告(pyproject.toml)**:寫**寬鬆範圍**(`requests>=2.28`)——你需要什麼。
- **鎖定(lock 檔)**:記**精確版本 + 雜湊**——實際裝了什麼;從 lock 精確重建。

**app vs library**:

- **application**:**釘精確版本**(要完全可重現的部署)。
- **library**:用**寬鬆範圍**(讓使用者能與其他套件共存,避免版本衝突)。

**追問**:直接相依 vs **傳遞相依**(lock 鎖定所有);`pip freeze`/requirements.txt 的缺陷(不分直接/傳遞、無雜湊),lock 檔更好;相依衝突(`ResolutionImpossible`)靠 pip 回溯 resolver、`pip check`。現代 uv/poetry 自動管 lock。

---

## Q2. uv/poetry 解決什麼問題?

**考點**:uv/poetry([03-uv-poetry](../chapters/13-tooling-packaging/03-uv-poetry.md))

**答**:它們把「**環境 + 套件 + lock + 打包**」整合成**一個工具**,取代 `pip + venv + requirements` 的手動組合:

- **uv**(Rust、**比 pip 快 10-100 倍**、整合度高,甚至能自己下載 Python)——近年最受矚目。
- **poetry**(成熟、pyproject 導向)。

工作流:`uv add`(加相依)→ `uv sync`(裝)→ `uv run`(執行)。**lock 檔自動管理 + 進版控**(可重現)。

**追問**:新專案建議 uv、poetry 也是好選擇、簡單專案 pip 也行。這些工具自動化了「宣告 vs 鎖定」的分離(Q1)。環境管理有兩維度:**套件隔離(venv)+ Python 版本管理(pyenv/uv)**,`.python-version` 記錄版本進版控。

---

## Q3. `pyproject.toml` 是什麼?有哪些主要區段?

**考點**:pyproject.toml([04-pyproject-toml](../chapters/13-tooling-packaging/04-pyproject-toml.md))

**答**:`pyproject.toml`(PEP 518/621)是**現代 Python 專案的單一設定中心**,取代 setup.py + setup.cfg + 各種 .ini。主要區段:

```toml
[project]                          # 元資料、相依、Python 版本
name = "myapp"
dependencies = ["requests>=2.28"]

[project.optional-dependencies]    # dev/test 群組
dev = ["pytest", "ruff", "mypy"]

[project.scripts]                  # CLI 進入點
mycli = "myapp.cli:main"

[build-system]                     # 建置後端
requires = ["setuptools"]

[tool.ruff]                        # 工具設定集中
line-length = 100
```

**追問**:`optional-dependencies` 分離核心與開發相依(`pip install -e ".[dev]"`);工具設定集中 `[tool.*]`(ruff/mypy/pytest,團隊/CI 一致);build backend(setuptools/hatchling/poetry-core)。

---

## Q4. 打包發佈流程?wheel 和 sdist 差在哪?

**考點**:打包([05-packaging](../chapters/13-tooling-packaging/05-packaging.md))

**答**:流程:**`python -m build`(產生 wheel + sdist)→ `twine check`/`upload`(或 uv/poetry publish)→ PyPI → 使用者 `pip install`**。

- **wheel(.whl)**:**預建**、安裝快、**主要格式**(直接解壓即用)。
- **sdist(.tar.gz)**:**原始碼**、後備(需在使用者端建置)。

**追問**:

- **版本?** → **語意化版本 SemVer**:major(破壞)/minor(新功能)/patch(修 bug)。
- **實務?** → 先上 **TestPyPI 驗證**(PyPI 版本**不可覆蓋**);用 **API token/OIDC** 認證(不用密碼);注意供應鏈安全(帳號保護、typosquatting)。前提是 pyproject.toml 完整 + src layout。

---

## Q5. formatter 和 linter 差在哪?ruff 為什麼紅?

**考點**:ruff([06-ruff-black](../chapters/13-tooling-packaging/06-ruff-black.md))

**答**:

- **formatter(排版)**:統一格式(縮排、換行、引號),**不改邏輯**(black、`ruff format`)。
- **linter(檢查)**:抓問題/可疑寫法/潛在 bug(未用 import、可簡化)(flake8、`ruff check`)。

兩者**互補**。**ruff(Rust 寫、快數十倍)一個工具同時做 lint + format**,取代 black + isort + flake8 + pyupgrade——**速度 + 整合**是它快速普及的主因。

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]   # 規則類別
```

**追問**:`--fix` 自動修;**CI 用 `--check`**(只驗證不改檔);三層把關(編輯器存檔自動 → pre-commit → CI)。

---

## Q6. mypy 怎麼導入既有專案?

**考點**:mypy 工程([07-mypy-tooling](../chapters/13-tooling-packaging/07-mypy-tooling.md))

**答**:

- **新專案**:直接 `strict = true`。
- **既有專案**:**漸進導入**——先讓 mypy 能跑(容忍現有錯誤)→ 擋住**新**錯誤 → 逐步清理舊模組 → 最終全 strict。**「別讓完美擋住開始」**。

**追問**:strict 展開的重要選項(`disallow_untyped_defs`、`no_implicit_optional`);第三方無型別先裝 **type stub**(`types-requests`)否則 `ignore_missing_imports`;**mypy 進 CI + pre-commit**(否則型別會腐爛);`# type: ignore[code]` 帶代碼 + `warn_unused_ignores`。mypy(靜態)+ pydantic(執行期)互補。

---

## Q7. pre-commit 是什麼?和 CI 的關係?

**考點**:pre-commit([08-pre-commit](../chapters/13-tooling-packaging/08-pre-commit.md))

**答**:pre-commit 在 **`git commit` 前自動跑檢查**(ruff/mypy/通用),**不通過就擋下提交**——把品質檢查自動化到 commit 這一刻,擋不合格程式進版控。設定 `.pre-commit-config.yaml`(宣告 hook)+ `pre-commit install`(裝 git hook),之後自動跑(只查改動檔)。

**與 CI 互補**:

| | pre-commit | CI |
|---|-----------|-----|
| 位置 | 本地 | 伺服器 |
| 速度 | 快(只查改動) | 完整 |
| 時機 | commit 前(第一道) | PR(最終) |
| 可繞過? | **可**(`--no-verify`) | 不可 |

所以 **CI 也該跑 pre-commit**(防繞過)。**三層品質把關**:編輯器(即時)→ pre-commit(commit 前)→ CI(PR)。

**追問**:可加密鑰偵測(detect-secrets)防密鑰進版控。

---

## Q8. 為什麼做 CLI 要用框架而非手讀 `sys.argv`?argparse/click/typer 差在哪?

**考點**:CLI([09-cli-apps](../chapters/13-tooling-packaging/09-cli-apps.md))

**答**:框架自動處理**型別轉換、驗證、`--help`、子命令、清楚的錯誤訊息、退出碼**——手讀 `sys.argv` 全要自己刻且容易錯。

| 工具 | 風格 | 定位 |
|------|------|------|
| **argparse** | 命令式 | 標準庫、零依賴 |
| **click** | 裝飾器 | 功能豐富 |
| **typer** | 型別註解 | 現代(建在 click 上) |

**追問**:CLI 組成(位置參數、選項/旗標、子命令、`--help`、退出碼);**解析與邏輯分離**以利測試(`run(argv)`);**退出碼 + stdout/stderr 分流**對 shell/CI/管線重要;用 `[project.scripts]` 打包成終端指令。

---

⬅️ [Part 12](part12-testing.md) ｜ [索引](README.md) ｜ ➡️ [Part 14 Web 開發](part14-web.md)
