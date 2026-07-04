# Part 01 面試題:入門與 Python 執行模型

> 對應 [Part 01 入門](../chapters/01-getting-started/README.md)。每題附「**面試官想聽到的完整回答**」、**追問(follow-up)** 與必要的程式碼。建議先自己答一遍再看解答。

---

## Q1. Python 是編譯式還是直譯式語言?

**考點**:執行模型([12-how-python-runs](../chapters/01-getting-started/12-how-python-runs.md))

**答**:**兩者都是**。CPython 先把原始碼**編譯成 bytecode**(位元組碼),再由 **PVM(Python Virtual Machine)逐條直譯這些 bytecode** 執行。完整管線是:

```text
原始碼 → tokenize → parse → AST → compile → bytecode →(PVM 逐條執行)→ 結果
```

這和 **JVM 架構類似**(Java 也是先編成 bytecode 再由 VM 執行)。所以「編譯 vs 直譯」是假二分——Python 有編譯步驟(產生 bytecode),但最終是直譯執行 bytecode。

**追問**:

- **為什麼 Python 相對慢?** → 因為 **PVM 逐條直譯 bytecode 有開銷**(每條指令都要 dispatch、堆疊操作),不像 C 直接跑機器碼。
- **這是語言規範還是實作?** → 是 **CPython 的實作細節**,非語言規範強制。PyPy 用 **JIT** 就把熱點編成機器碼,快很多。
- **能證明嗎?** → 用 `dis` 反組譯看 bytecode:

```python
import dis
dis.dis(lambda x: x + 1)
#   LOAD_FAST   x
#   LOAD_CONST  1
#   BINARY_OP   +
#   RETURN_VALUE   ← PVM 是堆疊式虛擬機
```

---

## Q2. `if __name__ == "__main__":` 是什麼?為什麼要用?

**考點**:必考題([03-repl-and-first-program](../chapters/01-getting-started/03-repl-and-first-program.md))

**答**:`__name__` 是每個模組的內建變數。當檔案被**直接執行**(`python file.py`)時,`__name__` 是 `'__main__'`;當檔案被 **import** 時,`__name__` 是模組名(如 `'file'`)。

`if __name__ == "__main__":` 這道「開關」讓一個檔案能**同時當腳本與模組**:直接跑時執行腳本邏輯,被 import 時**不觸發**那段邏輯(因為 import 會執行整個模組——見 Q3)。

```python
def add(a, b):
    return a + b

if __name__ == "__main__":   # 只在直接執行時跑,import 時不跑
    print(add(1, 2))
```

**追問**:

- **不加會怎樣?** → import 這個模組時,底下的腳本邏輯(如 `print`、跑測試、啟動伺服器)會被**意外執行**,因為 import 會執行整個檔案。
- **`python file.py` 和 `python -m file` 差在哪?** → 前者直接執行檔案(`__name__='__main__'`);`-m` 以模組方式執行(會先做 package 初始化,相對 import 才正常,見 [Q7](#q7-module-和-package-差在哪init py-做什麼))。

---

## Q3. `import` 一個模組時,底層發生了什麼?

**考點**:import 機制([06-modules-and-import](../chapters/01-getting-started/06-modules-and-import.md))

**答**:四個步驟:

1. **查 `sys.modules` 快取**:已 import 過就直接拿,不重跑。
2. **沿 `sys.path` 搜尋**:找不到就 `ModuleNotFoundError`。
3. **執行整個模組檔案**:由上到下跑一遍(所以頂層的程式碼會被執行)。
4. **快取並綁定名稱**:存進 `sys.modules`,把名稱綁到當前命名空間。

兩個關鍵重點:**import 會執行對方**(所以需要 `if __name__ == "__main__"`),而且**同一模組只執行一次**(快取,第二次 import 直接拿)。

**追問**:

- **`ModuleNotFoundError` 的根因?** → 模組**不在 `sys.path` 裡**。
- **`import X` / `from X import y` / `from X import *` 差別?** → 分別把「模組物件 X」/「X 裡的 y」/「X 裡所有公開名稱」綁進命名空間。**避免 `import *`**——污染命名空間、來源不清、可能覆蓋既有名稱。
- **循環 import 怎麼發生?** → A import B、B 又 import A;通常代表**設計問題**(職責耦合),應重構或延遲 import。

---

## Q4. 為什麼要用虛擬環境(venv)?原理是什麼?

**考點**:環境隔離([05-venv](../chapters/01-getting-started/05-venv.md))

**答**:**為什麼**:隔離每個專案的相依套件,避免版本衝突(「相依地獄」——專案 A 要 Django 3、專案 B 要 Django 4),且不污染系統 Python。

**原理**:venv 建立一個**獨立的 `site-packages`**,並在 activate 時把自己塞進 **PATH 最前面**,讓 `python`/`pip` 指向這個環境。生命週期:

```bash
python -m venv .venv          # 建立
source .venv/bin/activate     # 啟用(Windows: .venv\Scripts\activate)
python -m pip install ...     # 裝套件(進環境的 site-packages)
deactivate                    # 離開
```

**追問**:

- **怎麼判斷在不在環境內?** → `sys.prefix != sys.base_prefix`(在環境內時兩者不同)。
- **`.venv` 要進版控嗎?** → **不要**;只把 `requirements.txt` 進版控(環境是拋棄式、可重現)。
- **CI/Docker 常怎麼用?** → 免 activate,**直接呼叫 `.venv/bin/python`**。加分:提 `uv` 等新一代工具。

---

## Q5. 「明明 `pip install` 了,卻 `import` 不到」——為什麼?怎麼解?

**考點**:pip 與 python 指向([04-pip-and-packages](../chapters/01-getting-started/04-pip-and-packages.md))

**答**:根因是 **`pip` 和 `python` 指向不同的 Python**——套件裝進了 A Python 的 `site-packages`,但你用 B Python 執行,自然 import 不到。

**解法**:用 **`python -m pip install`** 取代 `pip install`——`python -m pip` 保證「用**這個** python 的 pip」,裝到的就是這個 python 的 site-packages,指向一致。

**追問**:

- **怎麼查實際指向?** → `import sys; sys.executable`(當前 python 路徑)、`which python`/`Get-Command python`。
- **怎麼做環境可重現?** → `pip freeze > requirements.txt`,他人 `pip install -r requirements.txt`;正式專案要**釘住版本**。加分:`~=`(相容版本,如 `~=1.4` 允許 1.4.x)語意、供應鏈風險(仿冒套件 typosquatting)。

---

## Q6. Python 2 和 3 最核心的差異是什麼?

**考點**:字串模型([10-python2-vs-3](../chapters/01-getting-started/10-python2-vs-3.md))

**答**:**最核心的改變是字串模型**。Python 3 的 `str` 從「bytes」變成 **Unicode**,`bytes` 獨立成另一型別,且**不再隱式互轉**(2 會偷偷把 str/unicode 互轉,埋下編碼地雷)。這個改變讓 2→3 遷移浩大,因為幾乎所有 I/O(檔案、網路、DB)的字串處理都受影響。

其他高頻差異:`print` 從敘述變**函式**、`5/2` 變**真除法**(`//` 才截斷)、`raw_input`→`input`、`range`/`dict.keys()` 變**惰性**。

**追問**:

- **`from __future__ import` 幹嘛的?** → 讓舊版**預先採用**新行為(如 `from __future__ import division`),體現「漸進、可選」的演進哲學。
- **Python 2 還能用嗎?** → 已於 **2020 年 EOL**;Python 3 是**年度發布**節奏。
- **DeprecationWarning 的意義?** → 「**先警告再移除**」的演進紀律,正是 2→3 慘痛經驗的產物。

---

## Q7. module 和 package 差在哪?`__init__.py` 做什麼?

**考點**:模組與套件([07-packages-and-init](../chapters/01-getting-started/07-packages-and-init.md))

**答**:**module 是單一 `.py` 檔;package 是含有模組的資料夾**(傳統上放一個 `__init__.py`)。

`__init__.py` 的作用:**標記這是 regular package**、可為空、可用來 **re-export**(拉平對外介面,讓使用者 `from pkg import X` 而非 `from pkg.sub.mod import X`)、設定 `__all__`(控制 `import *` 匯出什麼)。

**追問**:

- **絕對 vs 相對 import?** → 絕對 `from pkg.sub import x`;相對 `from .sub import x`(`.`=當前 package、`..`=上一層)。PEP 8 **偏好絕對 import**。
- **為什麼「直接執行 package 內的檔案」相對 import 會失敗?** → 直接執行時該檔的 `__name__` 是 `'__main__'`、**沒有 parent package**,相對 import 無從解析。用 **`python -m pkg.module`** 解決。
- 加分:**namespace package**(無 `__init__.py`)的存在與適用場景(跨目錄拆分同一 package)。

---

## Q8. flat layout 和 src layout 差在哪?為什麼推薦 src layout?

**考點**:專案結構([09-project-layout](../chapters/01-getting-started/09-project-layout.md))

**答**:**flat layout** 把套件放在專案根目錄;**src layout** 把套件放進 `src/`。

**推薦 src layout**,因為它**強迫「安裝後再 import」**:測試時你 import 的是**已安裝**的套件,和使用者的環境一致,能**及早暴露打包/路徑問題**。

原理和 `sys.path` 有關:當前目錄會被自動加入 `sys.path`,所以 **flat layout 免安裝就能 import**——這反而是陷阱(測試環境 ≠ 使用者環境,打包漏檔到上線才爆)。src layout 因為套件不在根目錄,逼你 `pip install -e .`(editable install)後才能 import。

**追問**:

- **`pip install -e .` 的好處?** → editable install,改原始碼立即生效、不必重裝,同時模擬「已安裝」狀態。
- 加分:**repo 名 / import 套件名 / PyPI 發佈名**三者可以不同(如 repo `my-proj`、import `myproj`、PyPI `my-cool-proj`)。

---

## Q9. 判斷 `None` 為什麼要用 `is None` 而不是 `== None`?

**考點**:Pythonic 慣用法([08-pep8-and-style](../chapters/01-getting-started/08-pep8-and-style.md))

**答**:`is` 比較**身分(是不是同一個物件)**,`==` 比較**相等(值相等)**。`None` 是**單例**(整個程式只有一個 `None` 物件),用 `is None` 直接比身分,**又快又準**。用 `== None` 會呼叫 `__eq__`,而自訂類別可能**覆寫 `__eq__`** 讓 `== None` 回傳非預期結果(甚至誤判)。所以判 None 一律 `is None` / `is not None`。

**追問**:

- **舉幾個 Pythonic 慣用法?** → `enumerate`(取索引+值)、`zip`(平行迭代)、**truthiness 判空**(`if items:` 而非 `if len(items) > 0`)、推導式、`a, b = b, a`(交換)。理由:**更清楚表達意圖、更少出錯**。
- **PEP 8 命名慣例?** → 函式/變數 `snake_case`、類別 `PascalCase`、常數 `UPPER_SNAKE_CASE`、內部用單底線前綴 `_x`。
- **實務怎麼落實?** → 靠 **ruff/black 自動化**,設定放 `pyproject.toml`,不靠人工。

---

## Q10. 現代 Python 工具鏈有哪些角色?

**考點**:工具鏈([11-editor-and-tooling-setup](../chapters/01-getting-started/11-editor-and-tooling-setup.md))

**答**:四個角色:**linter**(抓風格/可疑寫法)、**formatter**(自動排版)、**type checker**(靜態型別檢查)、**test runner**(跑測試)。代表工具:**ruff**(同時做 lint + format,以速度著稱,目前主流)、**mypy**(型別檢查)、**pytest**(測試)。

價值:**把動態語言的執行期錯誤提前到編輯/靜態檢查期**——拼錯變數名、未用的 import、型別不符,不必等跑到才發現。

**追問**:

- **編輯器怎麼整合?** → 透過 **LSP** 接語言伺服器(Pylance/pyright);關鍵是**選對虛擬環境的直譯器**。
- **mypy 會在執行期擋型別嗎?** → **不會**。mypy 是**靜態檢查**,執行期 Python 仍是動態型別,型別註記不強制。
- **怎麼層層把關?** → 設定集中 `pyproject.toml`,配 **pre-commit + CI** 多道關卡。

---

## Q11. Python 和 CPython 是什麼關係?

**考點**:規範 vs 實作([02-install-and-interpreter](../chapters/01-getting-started/02-install-and-interpreter.md))

**答**:**Python 是語言規範**(語法、語意的定義);**CPython 是它的參考實作**(用 C 寫的直譯器),也是絕大多數人平常用的那個。其他實作有 PyPy(JIT,較快)、Jython(跑在 JVM)等。你平常 `python` 指的幾乎都是 CPython。

一次安裝 = **直譯器 + 標準庫 + pip 綁在一起**,所以不同 Python 版本各有各的套件(這也是為什麼要 [venv](#q4-為什麼要用虛擬環境venv原理是什麼))。

**追問**:

- **版本號怎麼看?** → `major.minor.micro`(如 3.12.4);minor 才有新特性,micro 是修 bug。選版要看**支援週期**。
- **怎麼確認實際用哪個?** → `python --version`、`which python`/`Get-Command python`、`sys.executable`。

---

## Q12. `.pyc` 檔和 `__pycache__` 是什麼?

**考點**:bytecode 快取([12-how-python-runs](../chapters/01-getting-started/12-how-python-runs.md))

**答**:`.pyc` 是 **bytecode 快取**,放在 `__pycache__/` 資料夾。當你 import 一個模組,CPython 把它編譯成 bytecode 後**快取成 `.pyc`**,下次 import 若原始碼沒變就**直接載入快取**、跳過編譯,**加速 import**。

特性:**帶 Python 版本標記**(不同版本各一份)、**可安全刪除**(下次會重建)、**只有被 import 的模組會產生**(直接執行的主腳本不會)。

**追問**:

- **刪掉會怎樣?** → 沒事,下次 import 自動重建(只是那次慢一點點)。
- **要進版控嗎?** → 不要,`__pycache__/` 應在 `.gitignore`。

---

⬅️ [回面試題庫索引](README.md)
