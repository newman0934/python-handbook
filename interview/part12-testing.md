# Part 12 面試題:測試

> 對應 [Part 12 測試](../chapters/12-testing/README.md)。核心:pytest fixture/parametrize、mock 的 patch 陷阱、覆蓋率的誤解、TDD、屬性測試。

---

## Q1. 為什麼要寫測試?測試金字塔是什麼?

**考點**:測試價值([01-why-testing](../chapters/12-testing/01-why-testing.md))

**答**:核心價值:**防回歸**(改動的安全網——「沒測試不敢改程式」)、**活文件**、**設計回饋**、**快速定位**、**信心**。

**測試金字塔**:大量**單元測試**(快、隔離)+ 適量**整合測試** + 少量 **E2E**(慢、脆)。別**倒金字塔**(一堆慢又脆的 E2E,少單元)。

**追問**:

- **測試結構?** → **AAA**(Arrange-Act-Assert)、一測試一件事、**FIRST**(Fast/Independent/Repeatable/Self-validating/Timely)。
- **該測什麼?** → 核心邏輯、邊界、錯誤處理、bug 修復。**覆蓋率高 ≠ 測得好**(見 Q7)。

---

## Q2. pytest 和 unittest 差在哪?為什麼 pytest 是社群標準?

**考點**:unittest vs pytest([02-unittest](../chapters/12-testing/02-unittest.md) / [03-pytest-basics](../chapters/12-testing/03-pytest-basics.md))

**答**:

| | unittest | pytest |
|---|----------|--------|
| 斷言 | `self.assertEqual` 等方法 | **裸 `assert`(智慧內省)** |
| 風格 | 類別(繼承 `TestCase`) | 函式導向 |
| 前置 | `setUp`/`tearDown` | **fixture(更彈性)** |
| 參數化 | 麻煩 | **`@parametrize` 簡潔** |
| 安裝 | 標準庫 | 需安裝 |

pytest 的殺手鐧是**裸 `assert` + 斷言內省**——`assert x == 5` 失敗時 pytest **顯示 x 的實際值**(不必用一堆 assertXxx 方法)。**pytest 能執行 unittest 測試**(既有測試無痛遷移)。

**追問**:pytest 常用——`pytest.raises`(測例外,`match=` 檢查訊息)、`pytest.approx`(浮點)、markers(skip/skipif/xfail);測試發現規則 `test_*.py`/`test_*` 函式;選項 `-v`/`-k`/`-x`/`--lf`。

---

## Q3. 什麼是 fixture?它比 setUp/tearDown 好在哪?

**考點**:fixture([04-fixtures](../chapters/12-testing/04-fixtures.md))

**答**:fixture 是 pytest 的**測試前置準備機制**,用**依賴注入**——測試函式的**參數名 = fixture 名**,pytest 自動注入其回傳值:

```python
@pytest.fixture
def db():
    conn = connect()
    yield conn        # yield 前 setup、提供給測試、yield 後 teardown
    conn.close()      # 保證執行(即使測試失敗)

def test_query(db):   # 參數名 db = fixture 名,自動注入
    assert db.query(...) == ...
```

**比 setUp/tearDown 好**:**可組合**(fixture 用 fixture)、**可設作用域**(function/module/session)、**conftest.py 跨檔共用**(自動可用不必 import)。

**追問**:作用域取捨(預設 function 隔離、大作用域省資源但要防污染);內建 fixture:`tmp_path`(臨時目錄)、`capsys`(抓輸出)、`monkeypatch`(替換)、`caplog`(抓日誌)。

---

## Q4. `@pytest.mark.parametrize` 做什麼?

**考點**:參數化([05-parametrize](../chapters/12-testing/05-parametrize.md))

**答**:**資料驅動測試**——一個測試函式 + 多組資料,pytest **展開成多個獨立案例**(各自執行/回報):

```python
@pytest.mark.parametrize("n, expected", [
    (0, 1), (1, 1), (5, 120), (10, 3628800),
])
def test_factorial(n, expected):
    assert factorial(n) == expected
```

好處:**減少重複、失敗清楚顯示哪組錯、加案例只需加一行、每組獨立**(一組失敗不影響其他)。

**追問**:用 `ids=` 命名案例;`pytest.param(marks=)` 對個別案例加 marker;**系統性涵蓋正常 + 邊界 + 錯誤案例**;可與 fixture 並用、可參數化 fixture 本身(`params=`)。

---

## Q5.(必考)mock 是什麼?patch 的經典陷阱是什麼?

**考點**:mock([06-mock](../chapters/12-testing/06-mock.md))

**答**:mock 用於**隔離外部依賴**(網路/DB/時間/隨機/第三方),讓單元測試**快、穩定、可重複、無副作用**。工具:`Mock`/`MagicMock`(假物件,設 `return_value`/`side_effect`)+ `patch`(暫時替換)+ `assert_called_*`(驗證互動)。

**經典陷阱:patch「使用處」不是「定義處」**——要 patch **被測模組裡引用該名字的地方**:

```python
# mymodule.py: from requests import get; def fetch(): return get(url)
# 測試:
@patch("mymodule.get")        # 對!patch mymodule 裡的 get
# @patch("requests.get")      # 錯!mymodule 已經 import 了自己的 get 參照
```

**追問**:

- **`side_effect`?** → 可模擬例外(`side_effect=TimeoutError`)、依輸入回傳。`monkeypatch` 是 pytest 的簡單替代。
- **別過度 mock**:只 mock **外部邊界**,別 mock 內部邏輯(否則綁死實作、重構就壞)。優先用**依賴注入**設計讓測試更乾淨。

---

## Q6.(必考)覆蓋率 100% 代表測試很好嗎?

**考點**:覆蓋率([07-coverage](../chapters/12-testing/07-coverage.md))

**答**:**不代表!** 覆蓋率量的是「程式碼**被執行**的比例」,**不量「有沒有正確驗證」**。一個**沒有 assert** 的測試也能達到 100% 覆蓋率(執行了程式但什麼都沒驗證):

```python
def test_add():
    add(1, 2)      # 執行了 → 覆蓋率算數,但沒 assert → 沒驗證任何東西!
```

**覆蓋率是「找漏測」的工具,不是「測試品質」的指標**。

**追問**:別追求 100%;設合理門檻防退化(CI);用**分支覆蓋率**(比行覆蓋更有意義);用 `term-missing`/HTML 報告**找漏測分支** → 補案例;`# pragma: no cover` 排除不值得測的程式。

---

## Q7. TDD 是什麼?它只是「先寫測試」嗎?

**考點**:TDD([08-tdd](../chapters/12-testing/08-tdd.md))

**答**:TDD 的循環:**Red**(寫一個失敗的測試)→ **Green**(寫剛好通過的最少程式)→ **Refactor**(在測試保護下改善)——一次一個小循環。

**TDD 是設計方法,不只是測試**:先寫測試**逼你定義需求、導向可測試(鬆耦合)的設計、避免過度設計(YAGNI)、永遠有保護網**。

**追問**:Green 只寫**剛好**通過的程式;**別跳過 Refactor**;**「修 bug 先寫一個重現它的失敗測試」** 是每個人都該用的 TDD 精神(修好後測試變綠、且防復發)。不是所有東西都適合嚴格 TDD,精神比形式重要。

---

## Q8. 屬性測試(property-based testing)和一般測試差在哪?

**考點**:屬性測試([11-property-based-testing](../chapters/12-testing/11-property-based-testing.md))

**答**:

- **範例測試**:你**手寫具體例子**(`assert add(2,3)==5`)——反映你的想像,但有**盲點**(想不到的邊界)。
- **屬性測試**:你**描述性質**,工具(Hypothesis)**自動生成大量輸入**去測——探索輸入空間、抓你想不到的邊界:

```python
from hypothesis import given, strategies as st
@given(st.lists(st.integers()))
def test_sort_idempotent(xs):
    assert sorted(sorted(xs)) == sorted(xs)   # 性質:排序冪等
```

常見性質 pattern:**往返**(encode→decode 還原)、**不變量**、**冪等**、**與參考實作對比(oracle)**。

**追問**:

- **收縮(shrinking)的價值?** → 找到失敗時,把反例**縮成最小、最易懂**的(如把一個 500 元素的失敗 list 縮成 `[0]`),「找到 bug」變「理解 bug」。
- **取代範例測試嗎?** → **補充而非取代**;對有明確性質的純函式最有效,常找到範例測試漏掉的邊界(空、0、重複、Unicode、極值)。

---

## Q9. 怎麼系統性除錯?traceback 怎麼讀?

**考點**:除錯([10-debugging](../chapters/12-testing/10-debugging.md))

**答**:**科學方法**:重現 → 定位(二分/traceback)→ 假設 → 驗證 → **修根因 + 加迴歸測試**。

**讀 traceback**:**先看最後一行**(出錯的位置與類型),再**由內而外**(由下往上)追呼叫鏈。

工具:`breakpoint()`/`pdb`(指令 n/s/c/p/w/bt)、post-mortem 檢視例外現場;**二分定位** + `git bisect`(找哪個 commit 引入 bug)。

**追問**:

- **互動除錯器 vs log 除錯?** → 本機複雜 bug 用 pdb;正式/偶發/時序問題用 log。
- **強調?** → **先重現**(寫成測試)、**修根因不修症狀**、用測試鎖住(防復發)。`faulthandler`(硬當機)、`-X dev`(開發模式)。

---

## Q10. doctest 是什麼?適合當主要測試框架嗎?

**考點**:doctest([09-doctest](../chapters/12-testing/09-doctest.md))

**答**:doctest 讓 docstring 裡的範例「**既是文件又是測試**」——掃 `>>>` 範例、執行、驗證輸出,確保**文件範例不過期**:

```python
def add(a, b):
    """
    >>> add(2, 3)
    5
    """
    return a + b
```

**定位**:**適合文件範例驗證,不適合當主要測試框架**(複雜測試、fixture、mock 用 pytest)——兩者**互補**。

**追問**:陷阱是**輸出格式要完全一致**(dict 順序、浮點、記憶體位址、空白),用 `+ELLIPSIS`/`+NORMALIZE_WHITESPACE` 放寬;用 `pytest --doctest-modules` 一起跑。

---

⬅️ [Part 11](part11-stdlib.md) ｜ [索引](README.md) ｜ ➡️ [Part 13 工程化與打包](part13-tooling-packaging.md)
