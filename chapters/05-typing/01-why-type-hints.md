# 為什麼需要型別註記

> 型別註記不改變程式的執行行為——Python 執行期照樣不檢查。它們的價值在「執行之前」：讓工具抓錯、讓 IDE 補全、讓程式碼自我說明。這是動態語言補回靜態保障的方式。

## Why（為什麼）

Python 是動態型別（見 [動態型別](../02-fundamentals/01-dynamic-typing.md)），彈性高，但代價是「型別錯誤要執行到那一行才爆」。專案一大，這變成隱患：一個藏在少走分支裡的 `None` 傳給了期待 `str` 的函式，可能上線後才炸。**型別註記（type hints，PEP 484）** 讓你在程式裡標記「這裡應該是什麼型別」，配合 mypy 等工具在**編輯/CI 階段**就抓出型別不符——把動態語言缺的靜態保障補回來，而且不犧牲執行期的彈性。

## Theory（理論：漸進式型別）

Python 採用**漸進式型別（gradual typing）**：型別註記是**可選的**，你可以：

- 完全不寫（純動態，和以前一樣）。
- 只在關鍵處寫（公開 API、複雜函式）。
- 全面寫（大型專案、`strict` 模式）。

關鍵原則：**型別註記在執行期預設「不被強制」**。Python 直譯器**不會**因為你把 `int` 傳給標註 `str` 的參數而報錯——註記只是「給人與工具看的中繼資料」。真正做檢查的是**外部工具**（mypy、pyright），它們在不執行程式的情況下做**靜態分析**。

這是刻意的設計：保留動態語言的彈性與鴨子型別，同時讓想要靜態保障的人能漸進採用。

## Specification（規範：註記的三個層面）

```python
# 1. 變數註記
name: str = "Alice"
count: int = 0

# 2. 函式參數與回傳
def greet(name: str, times: int = 1) -> str:
    return f"Hi {name} " * times

# 3. 執行期可讀取（存在 __annotations__）
greet.__annotations__     # {'name': <class 'str'>, 'times': <class 'int'>, 'return': <class 'str'>}
```

註記不影響執行；`greet(123)` 照樣跑（可能出錯或不出錯），但 mypy 會警告。

## Implementation（註記不強制、工具才檢查、三大價值）

### 執行期不強制——證明給你看

```pycon
>>> def double(x: int) -> int:
...     return x * 2
>>> double("ab")            # 標註 int，但傳 str
'abab'                      # 照樣執行！註記沒擋，str * 2 剛好合法
>>> double([1])             # 傳 list
[1, 1]                      # 也跑（list * 2）
```

Python **不檢查**註記，`double("ab")` 正常執行。但 mypy 會說 `error: Argument 1 to "double" has incompatible type "str"; expected "int"`。**註記的價值在執行前，不在執行時。**

（少數情況註記會被執行期使用：dataclass、pydantic、`typing.get_type_hints`——但那是那些工具主動讀取註記，不是 Python 強制檢查。）

### 三大價值

**價值一：靜態抓錯（最重要）**。工具在你打字/CI 時抓出型別不符、`None` 誤用、拼錯屬性、傳錯參數——把 bug 提前到執行前：

```python
def get_user(id: int) -> User | None:
    ...

user = get_user(1)
print(user.name)     # mypy 警告：user 可能是 None！（漏了檢查）
```

**價值二：IDE 支援**。有了型別，IDE 能精準自動補全、跳轉定義、即時提示——`user.` 會列出 User 的屬性方法。無型別時 IDE 只能瞎猜。

**價值三：自我說明的文件**。`def process(items: list[dict[str, int]]) -> pd.DataFrame` 一看就懂輸入輸出，勝過一段註解，且**永遠與程式同步**（不像註解會過期）。

### 註記存在 `__annotations__`

```pycon
>>> def f(x: int) -> str: ...
>>> f.__annotations__
{'x': <class 'int'>, 'return': <class 'str'>}
```

框架（dataclass、pydantic、FastAPI）就是讀這個來運作——這是註記少數的「執行期用途」。

## Code Example（可執行的 Python 範例）

```python
# why_types_demo.py
from __future__ import annotations


def calculate_total(prices: list[float], tax_rate: float = 0.05) -> float:
    """型別註記讓介面一目了然，且工具能檢查呼叫是否正確。"""
    subtotal = sum(prices)
    return subtotal * (1 + tax_rate)


def find_user(users: dict[int, str], user_id: int) -> str | None:
    """回傳可能是 None——註記強迫呼叫端處理。"""
    return users.get(user_id)


def demo() -> None:
    # 正確使用
    total = calculate_total([100.0, 50.0, 25.0])
    print(f"含稅總額: {total:.2f}")

    users = {1: "Alice", 2: "Bob"}
    name = find_user(users, 1)
    # 因為回傳 str | None，好的程式會檢查
    if name is not None:
        print(f"找到: {name.upper()}")
    else:
        print("查無此人")

    # 註記存在 __annotations__（框架可讀取）
    print(f"註記: {calculate_total.__annotations__}")


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python why_types_demo.py
含稅總額: 183.75
找到: ALICE
註記: {'prices': list[float], 'tax_rate': <class 'float'>, 'return': <class 'float'>}
```

> 用 mypy 檢查這支程式：`mypy why_types_demo.py` → `Success`。若把 `calculate_total("x")` 加進去，mypy 會在執行前就報錯。

## Diagram（圖解：註記在何時發揮作用）

```mermaid
flowchart LR
    A[寫程式 + 型別註記] --> B[編輯期: IDE 補全/提示]
    B --> C[CI/commit 前: mypy 靜態檢查抓錯]
    C --> D[執行期: Python 不檢查註記, 照常跑]
    style B fill:#e8f5e9
    style C fill:#e8f5e9
    style D fill:#fff3e0
```

## Best Practice（最佳實踐）

- **公開 API、函式簽章一定加註記**：參數與回傳型別是最有價值的地方（別人靠它理解與呼叫）。
- **漸進採用**：既有專案先標關鍵模組，逐步擴大；新專案直接 `strict`。
- **把 mypy 納入 CI**：註記沒有檢查器就只是註解；靠 mypy/pyright 真正發揮價值（見 [mypy](07-mypy.md)）。
- **用註記表達「可能是 None」**：`X | None` 強迫呼叫端處理，消滅一大類 `AttributeError`。
- **別過度註記顯而易見的區域變數**：`x: int = 0` 多半多餘（型別可推斷）；重點在函式邊界。
- **註記要誠實**：標了型別就要符合；騙人的註記比沒有更糟（誤導工具與讀者）。

## Common Mistakes（常見誤解）

- **以為 Python 會執行期檢查註記**：不會。`double("x")` 照跑；檢查靠 mypy。想要執行期驗證用 pydantic（見 [Part 14](../14-web/06-pydantic-validation.md)）。
- **寫了註記卻不跑 mypy**：等於只寫了「會過期風險較低的註解」，抓不到錯。
- **註記與實際不符**：標 `-> int` 卻回傳 `None`，誤導所有人和工具。
- **過度註記**：每個區域變數都標，雜訊多；重點是函式邊界與複雜結構。
- **混淆型別註記與 pydantic/dataclass 的「執行期驗證」**：前者靠工具靜態檢查，後者是框架主動讀註記做執行期驗證。
- **以為註記會拖慢程式**：執行期幾乎零成本（只是中繼資料）。

## Interview Notes（面試重點）

- 說得出型別註記是 **PEP 484 的漸進式型別**，**執行期預設不強制**，由 **mypy/pyright 等外部工具靜態檢查**。
- 講得出三大價值：**靜態抓錯、IDE 支援、自我說明文件**。
- 能區分**靜態型別檢查（mypy，不執行程式）vs 執行期驗證（pydantic，主動讀註記驗證）**。
- 知道註記存在 **`__annotations__`**，是 dataclass/pydantic/FastAPI 等框架的執行期用途。
- 知道「寫了註記但沒跑檢查器」等於白寫，且註記不影響執行效能。

---

➡️ 下一章：[基本型別註記](02-basic-annotations.md)

[⬆️ 回 Part 5 索引](README.md)
