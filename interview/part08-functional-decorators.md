# Part 08 面試題:函數式與裝飾器

> 對應 [Part 08 函數式與裝飾器](../chapters/08-functional-decorators/README.md)。**裝飾器是面試必考**——本質、`wraps`、帶參數三層結構、`lru_cache` 都是高頻題。

---

## Q1. 「函式是一等公民」是什麼意思?

**考點**:一等公民([01-first-class-functions](../chapters/08-functional-decorators/01-first-class-functions.md))

**答**:因為**函式是物件**,所以可**賦值、當引數傳遞、當回傳值、存進容器**。`f` 是函式物件本身,`f()` 是呼叫它——**傳遞函式不加括號**。

應用:回呼(`sorted(key=f)`、`map`)、**分派表**(用 dict 取代冗長 if/elif)、策略模式:

```python
handlers = {"add": add, "sub": sub}    # 分派表
handlers[op](a, b)                     # 取代 if op=="add": ... elif ...
```

**追問**:函式有屬性(`__name__`/`__doc__`),這是**裝飾器**運作的基礎(裝飾器 = 接收並回傳函式)。

---

## Q2.(必考)什麼是裝飾器?`@deco` 展開成什麼?

**考點**:裝飾器本質([03-decorator-basics](../chapters/08-functional-decorators/03-decorator-basics.md))

**答**:裝飾器是**接收函式、回傳(包裝後的)函式的高階函式**。`@deco` 是 **`foo = deco(foo)`** 的語法糖,建立在**閉包**之上:

```python
import functools
def timer(func):
    @functools.wraps(func)                # 必加!
    def wrapper(*args, **kwargs):         # 用 *args/**kwargs 通用轉發
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__}: {time.perf_counter()-start:.4f}s")
        return result                     # 別忘了回傳結果
    return wrapper

@timer
def slow(): ...      # 等同 slow = timer(slow)
```

**追問**:

- **為什麼要 `@functools.wraps(func)`?** → 否則包裝後函式的 `__name__`/`__doc__`/簽章會變成 wrapper 的(遺失原函式的元資訊,debug/自省/文件都出錯)。
- **用途?** → 日誌、計時、快取、重試、權限、路由註冊。加分:用 `ParamSpec` 保留型別簽章(見 [Part 05](part05-typing.md#q10裝飾器包裝函式後型別簽章會不見怎麼保留self-有什麼用))。

---

## Q3.(必考)帶參數的裝飾器 `@retry(times=3)` 是怎麼運作的?

**考點**:帶參數裝飾器([04-decorator-with-args](../chapters/08-functional-decorators/04-decorator-with-args.md))

**答**:**三層結構**:

```python
def retry(times):                    # 外層:收「裝飾器參數」
    def decorator(func):             # 中層:收「被裝飾的函式」
        @functools.wraps(func)
        def wrapper(*args, **kwargs): # 內層:包裝器
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if i == times - 1: raise
        return wrapper
    return decorator

@retry(times=3)      # 先呼叫 retry(3) 得到 decorator,再 decorator(func)
def flaky(): ...
```

**關鍵**:`@retry(times=3)` **有括號**——先**呼叫** `retry(3)` 得到真正的裝飾器,再套用到函式。對比 `@deco`(無括號,直接 `deco(func)`)。

**追問**:每層透過**閉包**捕捉上層變數(`wrapper` 用到 `times` 和 `func`)。中層也要 `@wraps`、內層轉發 `*args/**kwargs`。加分:「帶/不帶參數兩用」的 `func=None` 模式。

---

## Q4.(高頻)`functools.lru_cache` 做什麼?有什麼限制?

**考點**:functools([05-functools](../chapters/08-functional-decorators/05-functools.md))

**答**:`@lru_cache`(或 `@cache`)是**記憶化(memoization)**——快取函式的回傳值,相同引數直接回快取。讓費氏遞迴從 **O(2ⁿ) 變 O(n)**:

```python
from functools import lru_cache
@lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n-1) + fib(n-2)   # 不快取會指數爆炸
```

**限制**:

- **引數必須 hashable**(要當快取的 key)——不能傳 list/dict。
- **函式必須是純函式**(相同輸入永遠相同輸出、無副作用)——否則快取會給錯結果。
- **`maxsize` 控記憶體**(LRU 淘汰最久沒用的);`cache` 是無上限版。

**追問**:`cache_info()`/`cache_clear()` 監控與清除。其他 functools:`total_ordering`(由 `__eq__` + 一個比較補齊全套比較方法)、`singledispatch`(依第一參數型別分派)。

---

## Q5. `functools.partial` 和 lambda 差在哪?

**考點**:partial([06-partial](../chapters/08-functional-decorators/06-partial.md))

**答**:`partial` 做**偏函式應用**——固定部分參數,回傳一個參數較少的新可呼叫物件:

```python
from functools import partial
int2 = partial(int, base=2)     # 固定 base=2
int2("1010")                     # 10
```

**partial vs lambda**:

| | partial | lambda |
|---|---------|--------|
| 可內省 | ✓(`.func`/`.args`/`.keywords`) | ✗ |
| 可 pickle/序列化 | ✓ | ✗ |
| 意圖清楚 | ✓ | 較模糊 |
| 額外邏輯 | ✗ | ✓ |

**追問**:

- **典型場景?** → 回呼預綁參數、**multiprocessing**(lambda 不能 pickle,partial 可以)。
- **固定參數規則?** → 位置參數**從左填**,要固定後面的用關鍵字。PEP 8 建議別把 lambda 綁名稱(partial 更好)。

---

## Q6. 高階函式有哪些?Python 為什麼偏好推導式勝過 `map`/`filter`?

**考點**:高階函式([02-higher-order-functions](../chapters/08-functional-decorators/02-higher-order-functions.md))

**答**:**高階函式**接收/回傳函式:`map`、`filter`、`functools.reduce`、`sorted(key=)`。`map`/`filter` **惰性、一次性、可多序列**;`reduce` 被移到 `functools`(Python 3 刻意降級)。

**Python 偏好推導式**,因為 `map`/`filter` + **lambda** 較不可讀,推導式更清楚:

```python
[x*2 for x in xs if x > 0]        # Pythonic
list(map(lambda x: x*2, filter(lambda x: x > 0, xs)))   # 囉嗦
```

但 `map` 傳**具名函式**時(`map(str, nums)`)是例外(反而簡潔)。

**追問**:聚合優先用 `sum`/`max`/`min`/`accumulate`,`reduce` 能不用就不用。`filter(None, it)` 過濾 falsy;`reduce` 空序列需初始值。

---

## Q7. 類別也能當裝飾器?`@dataclass` 是什麼裝飾器?

**考點**:類別裝飾器([07-class-decorators](../chapters/08-functional-decorators/07-class-decorators.md))

**答**:有兩種「類別 + 裝飾器」:

- **裝飾類別**(接收類別、回傳類別):如 **`@dataclass`**——讀型別註記、自動加 `__init__`/`__repr__`/`__eq__`、回傳增強的類別。可做「**自動註冊**」,是 metaclass 的輕量替代。
- **類別作為裝飾器**(實例透過 `__call__` 當裝飾器):用**實例屬性保存狀態**(如計數、統計):

```python
class CountCalls:
    def __init__(self, func):
        self.func = func
        self.count = 0
    def __call__(self, *args, **kwargs):    # 讓實例可當裝飾器用
        self.count += 1
        return self.func(*args, **kwargs)
```

**追問**:**類別裝飾器 vs 閉包裝飾器**取捨——需要複雜狀態/額外方法(`reset`/`stats`)用類別;簡單的用閉包。類別裝飾器要有 `__call__` 且處理 `wraps`;帶參數的用 `__init__`(參數)+ `__call__`(函式→包裝器)。

---

⬅️ [Part 07](part07-iterators-generators.md) ｜ [索引](README.md) ｜ ➡️ [Part 09 並發](part09-concurrency.md)
