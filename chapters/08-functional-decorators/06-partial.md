# partial 與偏函式

> `functools.partial` 把「先固定一部分參數」的函式做出來——`partial(int, base=2)` 就是「二進位版的 int」。它讓你從通用函式衍生出特化版本，是回呼與設定的利器。

## Why（為什麼）

常見需求：有個通用函式，但你想要「固定某些參數的特化版」。例如 `int(x, base=2)` 每次都寫 `base=2` 很煩，你想要一個「就是二進位」的 `to_binary`。或者傳回呼時想「預先綁好某些參數」。手寫一個 lambda 或 def 可以，但 `functools.partial` 更清楚、可內省、且是慣用做法。這章講 partial 的用法與它勝過 lambda 的地方。

## Theory（理論：偏函式應用）

**偏函式應用（partial application）** 是「把一個多參數函式，透過固定部分參數，變成參數較少的新函式」。`functools.partial(func, *args, **kwargs)` 回傳一個新的可呼叫物件——呼叫它時，會用「預先固定的參數 + 新傳入的參數」去呼叫原 `func`。

```python
from functools import partial

to_binary = partial(int, base=2)     # 固定 base=2
to_binary("1010")                    # = int("1010", base=2) = 10
```

`to_binary` 是 `int` 的「特化版」——`base` 已被綁定，只需傳字串。這在需要「帶預設設定的函式」或「預綁參數的回呼」時很有用。

## Specification（規範：partial 語法）

```python
from functools import partial

# 固定位置參數（從左邊開始填）
add = lambda a, b, c: a + b + c
add_10 = partial(add, 10)            # 固定第一個參數 a=10
add_10(20, 30)                       # = add(10, 20, 30) = 60

# 固定關鍵字參數
to_hex = partial(int, base=16)
to_hex("ff")                         # = int("ff", base=16) = 255

# 混合
greet = lambda greeting, name: f"{greeting}, {name}!"
hello = partial(greet, "Hello")      # 固定 greeting
hello("Alice")                       # "Hello, Alice!"

# partial 物件可內省
p = partial(int, base=2)
p.func        # int（原函式）
p.args        # ()（固定的位置參數）
p.keywords    # {'base': 2}（固定的關鍵字參數）
```

## Implementation（固定參數、當回呼、vs lambda）

### 固定位置參數（從左填）與關鍵字參數

```python
from functools import partial

def power(base: float, exponent: float) -> float:
    return base ** exponent

square = partial(power, exponent=2)   # 固定 exponent（用關鍵字較安全）
cube = partial(power, exponent=3)
square(5)      # 25
cube(2)        # 8

# 固定位置參數是「從左邊」填
def divide(a: float, b: float) -> float:
    return a / b
half = partial(divide, b=2)           # 固定 b（除以 2）
half(10)       # 5.0
```

**注意**：`partial` 固定位置參數是**從左邊開始**填。想固定「後面的」參數，用關鍵字（如 `partial(power, exponent=2)`），較不易錯。

### 當回呼：預綁參數

partial 最實用的場景之一是**傳回呼時預先綁定參數**：

```python
from functools import partial

def on_click(button_id: str, event: str) -> None:
    print(f"按鈕 {button_id} 收到 {event}")

# 為每個按鈕建立預綁 button_id 的回呼
save_handler = partial(on_click, "save")
cancel_handler = partial(on_click, "cancel")

# 事件系統只需傳 event，button_id 已綁好
save_handler("click")      # 按鈕 save 收到 click
```

比每個按鈕寫一個 lambda 清楚，且回呼函式的來源（`on_click`）可透過 `partial.func` 內省。

### partial vs lambda

partial 和 lambda 常能互換，但各有優勢：

```python
# 這兩者效果相同：
square = partial(power, exponent=2)
square = lambda base: power(base, exponent=2)
```

| | `partial` | `lambda` |
|--|-----------|----------|
| 可內省 | ✅（`.func`/`.args`/`.keywords`） | ❌（只是 `<lambda>`） |
| 可 pickle（序列化） | ✅（若原函式可） | ❌ |
| 清楚表達「固定參數」 | ✅ | 靠讀者理解 |
| 需要額外邏輯 | ❌（只能固定參數） | ✅（可寫運算式） |

**準則**：**單純「固定參數」用 `partial`**（可內省、可序列化、意圖清楚）；需要「額外運算/轉換」才用 lambda。PEP 8 也建議不要把 lambda 綁到名稱（見 [lambda](../02-fundamentals/10-lambda.md)），這時 partial 是更好的選擇。

### 也能用在方法與其他可呼叫物件

`partial` 對任何可呼叫物件都行（函式、方法、類別、其他 partial）：

```python
from functools import partial
Point = partial(dict, x=0, y=0)      # 帶預設的 dict 工廠
Point(z=5)                            # {'x': 0, 'y': 0, 'z': 5}
```

## Code Example（可執行的 Python 範例）

```python
# partial_demo.py
from __future__ import annotations

from functools import partial


def power(base: float, exponent: float) -> float:
    return base**exponent


def log(level: str, message: str) -> str:
    return f"[{level}] {message}"


def demo() -> None:
    # 1. 固定參數建特化版
    square = partial(power, exponent=2)
    cube = partial(power, exponent=3)
    print(f"square(5) = {square(5)}")       # 25
    print(f"cube(2) = {cube(2)}")           # 8

    # 2. int 的進位特化版
    to_binary = partial(int, base=2)
    to_hex = partial(int, base=16)
    print(f"二進位 '1010' = {to_binary('1010')}")   # 10
    print(f"十六進位 'ff' = {to_hex('ff')}")         # 255

    # 3. 預綁參數的 logger
    info = partial(log, "INFO")
    error = partial(log, "ERROR")
    print(info("系統啟動"))
    print(error("連線失敗"))

    # 4. partial 可內省
    print(f"square.func = {square.func.__name__}")
    print(f"square.keywords = {square.keywords}")


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python partial_demo.py
square(5) = 25
cube(2) = 8
二進位 '1010' = 10
十六進位 'ff' = 255
[INFO] 系統啟動
[ERROR] 連線失敗
square.func = power
square.keywords = {'exponent': 2}
```

## Diagram（圖解：partial 固定參數）

```mermaid
flowchart LR
    A["power(base, exponent)"] -->|partial 固定 exponent=2| B["square(base)"]
    B -->|square(5)| C["呼叫 power(5, exponent=2) = 25"]
    style B fill:#e8f5e9
```

## Best Practice（最佳實踐）

- **單純固定參數用 `partial`**：比 lambda 更清楚、可內省（`.func`/`.args`/`.keywords`）、可序列化。
- **固定「後面的」參數用關鍵字**：`partial(f, kw=value)`，避免位置填錯（partial 從左填位置參數）。
- **回呼預綁參數用 partial**：為不同情境衍生預綁好的回呼，比一堆 lambda 清楚。
- **需要序列化（multiprocessing、pickle）用 partial 而非 lambda**：lambda 不能 pickle（見 [multiprocessing](../09-concurrency/05-multiprocessing.md)）。
- **需要額外邏輯才用 lambda 或 def**：partial 只能固定參數，不能加運算。
- **partial 可鏈接、可用於任何可呼叫物件**（函式、方法、類別工廠）。

## Common Mistakes（常見誤解）

- **固定位置參數時搞錯順序**：partial 從**左邊**填位置參數；想固定後面的用關鍵字。
- **該用 partial 卻硬寫 lambda 綁名稱**：`f = lambda x: g(x, base=2)` 不如 `f = partial(g, base=2)`（可內省、PEP 8 也建議）。
- **在 multiprocessing 用 lambda 當可呼叫物件**：lambda 不能 pickle，會出錯；用 partial 或具名函式。
- **以為 partial 能加邏輯**：它只固定參數，不能寫運算式/轉換；那用 lambda/def。
- **覆蓋已固定的關鍵字**：`partial(f, x=1)` 呼叫時再傳 `x=2` 會覆蓋（後傳的贏），有時是意外。
- **忘了 partial 回傳的是可呼叫物件不是函式**：`type()` 是 `partial`，但用起來一樣。

## Interview Notes（面試重點）

- 說得出 **`functools.partial` 做偏函式應用**：固定部分參數、回傳參數較少的新可呼叫物件。
- **能對比 partial vs lambda**：partial **可內省（`.func`/`.args`/`.keywords`）、可 pickle/序列化、意圖清楚**；lambda 能寫額外邏輯但不可內省/序列化。
- 知道 **partial 固定位置參數從左填**，固定後面的用關鍵字。
- 知道**回呼預綁、multiprocessing（lambda 不能 pickle）** 是 partial 的典型場景。
- 知道 partial 適用任何可呼叫物件，且 PEP 8 建議不把 lambda 綁名稱（partial 更好）。

---

➡️ 下一章：[類別裝飾器](07-class-decorators.md)

[⬆️ 回 Part 8 索引](README.md)
