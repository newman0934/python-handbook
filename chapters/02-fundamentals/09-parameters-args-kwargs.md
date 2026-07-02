# 參數、預設值、*args / **kwargs

> Python 的參數系統極其靈活：位置、關鍵字、預設值、`*args`、`**kwargs`、甚至強制位置或強制關鍵字——但這份彈性也藏著全 Python 最惡名昭彰的陷阱：可變預設參數。

## Why（為什麼）

函式怎麼「收」參數，決定了它好不好用、好不好維護。Python 給了非常豐富的參數形式，讓你能設計出既簡潔又清楚的介面（例如強制某些參數一定要用關鍵字寫，避免呼叫端一長串看不懂的位置引數）。同時，**可變預設參數** 是幾乎每個 Python 工程師都踩過、面試也必問的陷阱。這章把參數系統講全，並把那個陷阱徹底講清楚。

## Theory（理論：位置 vs 關鍵字）

呼叫函式時，引數（argument）有兩種傳法：

- **位置引數（positional）**：依順序對應，`f(1, 2)`。
- **關鍵字引數（keyword）**：依名稱對應，`f(a=1, b=2)`，順序無所謂。

定義端則能規定每個參數「能用哪種方式傳」。Python 3 提供 `/` 和 `*` 兩個分隔符，把參數列切成三段，精確控制介面。

## Specification（規範：完整參數語法）

```python
def f(pos_only, /, normal, *args, kw_only, **kwargs):
    ...
```

| 區段 | 位置 | 意義 |
|------|------|------|
| `pos_only` | `/` 之前 | **只能用位置**傳 |
| `normal` | `/` 與 `*` 之間 | 位置或關鍵字皆可 |
| `*args` | — | 收集多餘的**位置**引數成 tuple |
| `kw_only` | `*` 之後 | **只能用關鍵字**傳 |
| `**kwargs` | 最後 | 收集多餘的**關鍵字**引數成 dict |

常見的完整範例：

```python
def connect(host, port=5432, *, timeout=30, **options):
    # host：位置或關鍵字；port：有預設；
    # timeout：強制關鍵字（* 之後）；options：其餘關鍵字收進 dict
    ...

connect("localhost")                          # OK
connect("localhost", 5433, timeout=10)        # OK
connect("localhost", timeout=10, ssl=True)    # ssl 進 options
# connect("localhost", 5433, 10)              # ❌ timeout 不能用位置傳
```

## Implementation（`*`/`**` 的兩種角色 + 可變預設陷阱）

### `*` 和 `**` 在「定義」與「呼叫」的角色相反

**定義時**：`*args` / `**kwargs` 是**收集（打包）**多餘引數。

```python
def total(*args, **kwargs):
    print(args)     # tuple
    print(kwargs)   # dict

total(1, 2, 3, a=10, b=20)
# args   = (1, 2, 3)
# kwargs = {'a': 10, 'b': 20}
```

**呼叫時**：`*` / `**` 是**展開（解包）** 一個序列 / 對映成引數。

```python
def point(x, y, z):
    return x + y + z

coords = [1, 2, 3]
point(*coords)               # 等同 point(1, 2, 3)

kw = {"x": 1, "y": 2, "z": 3}
point(**kw)                  # 等同 point(x=1, y=2, z=3)
```

名字不必是 `args`/`kwargs`（那只是慣例），重點是 `*`（對序列/位置）與 `**`（對 dict/關鍵字）。

### 🔴 可變預設參數陷阱（Python 頭號經典 bug）

**預設值只在「函式定義時」求值一次，之後所有呼叫共用同一個物件。** 如果預設值是**可變物件**（list、dict、set），災難就來了：

```python
# ❌ 陷阱寫法
def append_to(item, target=[]):     # 這個 [] 只建立一次！
    target.append(item)
    return target

print(append_to(1))    # [1]
print(append_to(2))    # [1, 2]  ← 竟然累加！不是 [2]
print(append_to(3))    # [1, 2, 3] ← 每次呼叫共用同一個 list
```

第二次呼叫沒傳 `target`，卻拿到了上次殘留的內容——因為那個 `[]` 是**定義時建立、所有呼叫共用的同一個 list 物件**（可用 `append_to.__defaults__` 看到它）。

**正確做法：預設用 `None`，在函式內建立新物件：**

```python
# ✅ 正解
def append_to(item, target=None):
    if target is None:
        target = []          # 每次呼叫都建立新的
    target.append(item)
    return target

print(append_to(1))    # [1]
print(append_to(2))    # [2]  ← 正確！
```

這個 `if x is None:` 的慣用法，就是為了避開可變預設陷阱。**不可變預設值（`0`、`""`、`None`、`()`）沒有此問題**，因為它們無法被原地修改。

### 為什麼 Python 這樣設計？

預設值在定義時求值一次，是刻意的效能與一致性選擇（避免每次呼叫重算）。它本身不是 bug，只是與「可變物件」相遇時會咬人——這也是為什麼理解 [名稱綁定](01-dynamic-typing.md) 與 [可變性](../03-data-structures/06-mutability.md) 如此重要。

## Code Example（可執行的 Python 範例）

```python
# parameters_demo.py
def make_greeting(name: str, *, greeting: str = "Hello", punctuation: str = "!") -> str:
    """greeting、punctuation 為強制關鍵字參數（* 之後）。"""
    return f"{greeting}, {name}{punctuation}"


def collect(*args: int, **kwargs: str) -> str:
    """示範打包。"""
    return f"位置={args}, 關鍵字={kwargs}"


def bad_append(item, target=[]):        # noqa: B006 — 故意示範陷阱
    target.append(item)
    return target


def good_append(item, target=None):
    if target is None:
        target = []
    target.append(item)
    return target


def demo() -> None:
    # 強制關鍵字
    print(make_greeting("Alice"))                       # Hello, Alice!
    print(make_greeting("Bob", greeting="Hi", punctuation="."))

    # 打包 / 解包
    print(collect(1, 2, 3, mode="fast"))

    # 陷阱 vs 正解
    print("bad :", bad_append(1), bad_append(2))         # [1] [1, 2] ← 累加
    print("good:", good_append(1), good_append(2))       # [1] [2]   ← 正確


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python parameters_demo.py
Hello, Alice!
Hi, Bob.
位置=(1, 2, 3), 關鍵字={'mode': 'fast'}
bad : [1] [1, 2]
good: [1] [2]
```

## Diagram（圖解：可變預設參數為何累加）

```mermaid
flowchart TD
    A[def f item, target=[] 被定義] --> B[建立「一個」list 物件當預設]
    B --> C[第一次呼叫 f 1: 改到那個 list → [1]]
    C --> D[第二次呼叫 f 2: 還是同一個 list → [1,2]]
    D --> E[所有未傳 target 的呼叫共用它]
    style E fill:#ffebee
```

## Best Practice（最佳實踐）

- **可變預設值一律用 `None` 哨兵**：`def f(x=None): if x is None: x = []`。ruff 的 `B006` 規則會幫你抓 `def f(x=[])`。
- **用強制關鍵字參數提升可讀性**：布林旗標、選項類參數放在 `*` 之後，逼呼叫端寫 `sort(reverse=True)` 而非 `sort(True)`。
- **`*args`/`**kwargs` 用在真的需要不定量參數或轉發時**（如包裝別的函式），別濫用——它會讓函式簽章變模糊、失去型別檢查。
- **轉發參數用 `*args, **kwargs`**：裝飾器與包裝函式的標準手法（見 [functools 與 wraps](../08-functional-decorators/05-functools.md)）。
- **參數不要太多**：超過 3–4 個考慮用 dataclass / 設定物件聚合。
- **強制位置參數 `/`** 用於：想保留改參數名的自由、或效能敏感的底層 API；一般業務程式少用。

## Common Mistakes（常見誤解）

- **可變預設參數 `def f(x=[])` / `def f(d={})`**：跨呼叫共用同一物件，狀態殘留。用 `None` 哨兵。
- **以為預設值每次呼叫都重新求值**：只在**定義時**求值一次。
- **搞混定義與呼叫端的 `*`**：定義端是打包、呼叫端是解包。
- **在 `*args` 後放普通位置參數**：`*args` 後面的具名參數自動變成**強制關鍵字**，不能再用位置傳。
- **`**kwargs` 吃掉拼錯的參數名**：`connect(hst="x")` 不報錯，`hst` 默默進了 kwargs——用明確參數 + 型別檢查可避免。
- **解包時型別不符**：`f(**list_obj)` 會錯，`**` 只能展開對映。

## Interview Notes（面試重點）

- **可變預設參數是高頻必考題**：能說出「預設值定義時求值一次、可變物件跨呼叫共用」的原因，並寫出 `None` 哨兵的正解。
- 能說明**定義端 `*args/**kwargs` 是打包、呼叫端 `*/**` 是解包**。
- 知道 **`/`（強制位置）與 `*`（強制關鍵字）** 分隔符的作用與設計目的（介面清晰、保留改名自由）。
- 知道**強制關鍵字參數**能提升呼叫可讀性（避免神秘的位置布林）。
- 知道 `*args/**kwargs` 在**參數轉發**（裝飾器、包裝）的用途。

---

➡️ 下一章：[lambda 與匿名函式](10-lambda.md)

[⬆️ 回 Part 2 索引](README.md)
