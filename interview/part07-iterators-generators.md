# Part 07 面試題:迭代器與生成器

> 對應 [Part 07 迭代器與生成器](../chapters/07-iterators-generators/README.md)。核心:iterable/iterator 協定、生成器暫停恢復、惰性求值、yield from、生成器當協程。

---

## Q1. iterable 和 iterator 差在哪?`for` 迴圈底層做什麼?

**考點**:協定([01-iterable-iterator](../chapters/07-iterators-generators/01-iterable-iterator.md))

**答**:

- **iterable(可迭代物件)**:有 `__iter__`,能**要一個 iterator**,**可重複**遍歷(list/str/dict/set)。
- **iterator(迭代器)**:有 `__next__`(產出下一個)+ `__iter__`(回自己),**產出元素、一次性耗盡**。

`for` 的底層:

```python
it = iter(obj)          # 呼叫 __iter__ 取得 iterator
while True:
    try:
        x = next(it)    # 呼叫 __next__
    except StopIteration:  # 耗盡則結束
        break
    # 處理 x
```

**追問**:

- **為什麼生成器只能用一次?** → 生成器是 iterator,**一次性耗盡**,遍歷完就空了(要再用得重建)。
- **`next(it, default)`?** → 取下一個,耗盡時回 default 而非拋 StopIteration。

---

## Q2. 為什麼容器和迭代器要分離?兩者合一有什麼問題?

**考點**:iter/next 設計([02-iter-next](../chapters/07-iterators-generators/02-iter-next.md))

**答**:正確設計是**分離**:**容器**的 `__iter__` **每次回一個新的 iterator**;**iterator** 持有進度、`__next__` 產出、`__iter__` 回自己。

分離的好處:**可重複遍歷、可巢狀遍歷**(兩層 for 同一容器互不干擾,因為各有獨立 iterator)。

**容器兼當 iterator 的問題**:只能遍歷**一次**、巢狀遍歷會**互相干擾**(共用同一進度)。只有「一次性串流」才適合合一。

**追問**:最簡潔做法是**讓 `__iter__` 成為生成器**——自動獲得「每次回新 iterator」的分離好處:

```python
class Deck:
    def __iter__(self):
        for card in self._cards:
            yield card    # 生成器,每次呼叫回新的
```

---

## Q3. 什麼是生成器?它的核心優勢是什麼?

**考點**:生成器([03-generator](../chapters/07-iterators-generators/03-generator.md))

**答**:生成器是**含 `yield` 的函式**。呼叫它**不執行函式體**,而是回傳一個**生成器物件(iterator)**。`next`/`for` 時**執行到 `yield` 吐出值並暫停**,下次從斷點**恢復**(保留區域變數):

```python
def count_up(n):
    i = 0
    while i < n:
        yield i        # 吐值 + 暫停
        i += 1
```

核心優勢:**惰性求值**(值用到才算)+ **省記憶體**(不建整個 list)+ **能表示無限序列**。

**追問**:

- **生成器能遍歷幾次?** → **一次**(是 iterator,耗盡)。
- **生成器裡 `return`?** → 只**結束迭代**(值進 `StopIteration.value`),不像普通函式回傳值。無限生成器要配 `itertools.islice` 取前 N 個,別 `list()` 全取。

---

## Q4. 生成器表達式 `(x for x in xs)` 和 list 推導式 `[...]` 差在哪?

**考點**:生成器表達式([04-generator-expression](../chapters/07-iterators-generators/04-generator-expression.md))

**答**:生成器表達式 `(...)` 是**惰性版推導式**——回傳生成器、**一次產一個、記憶體恆定**;list 推導式 `[...]` **立刻建整個 list**、佔記憶體。

**餵給聚合函式最理想**(sum/any/all/max/join),當唯一引數時可省略括號:

```python
sum(x*x for x in range(10**6))   # 不建百萬元素 list
any(x > 100 for x in data)       # 短路,找到就停
```

**追問**:

- **何時用哪個?** → 多次遍歷/需索引/需長度 → list;只走一次/資料大 → 生成器。
- **`(...)` 是 tuple 嗎?** → **不是**,是生成器;一次性、不支援 len/索引。

---

## Q5. `yield from` 只是 `for x in it: yield x` 的語法糖嗎?

**考點**:yield from([05-yield-from](../chapters/07-iterators-generators/05-yield-from.md))

**答**:表面上等價,但**不只是語法糖**。`yield from iterable` 把子可迭代物件的所有值透傳出去,而且建立一個**透明通道**:

- 能**透傳 `send()`/`throw()`** 給子生成器(委派協程)。
- 能取得子生成器的 **`return` 值**(存在 `StopIteration.value`)。

```python
def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)   # 遞迴扁平化
        else:
            yield item
```

**追問**:用途——串接生成器、遞迴扁平化、委派 `__iter__`、組合協程。**`yield from` 是 `await` 的前身**(協程/asyncio 歷史)。遞迴扁平化注意 **str 也是 iterable** 的陷阱(會無限拆字元)。

---

## Q6. `itertools` 有哪些工具?`groupby` 有什麼陷阱?

**考點**:itertools([06-itertools](../chapters/07-iterators-generators/06-itertools.md))

**答**:三類(全部**惰性、C 實作、省記憶體**):

- **無限**:`count`(數不停)、`cycle`(循環)、`repeat`。
- **終止型**:`chain`(串接)、`islice`(切片)、`groupby`、`accumulate`(累計)、`pairwise`(相鄰對)。
- **組合型**:`product`(笛卡兒積)、`permutations`(排列)、`combinations`(組合)。

**`groupby` 陷阱**:**只分組「連續」相同 key** 的元素!所以**必須先排序**(按 key),否則同 key 分散各處會被切成多組。要保留組內容要 `list(g)`(g 也是惰性的)。

```python
from itertools import groupby
data = sorted(items, key=lambda x: x.dept)   # 先排序!
for dept, group in groupby(data, key=lambda x: x.dept):
    members = list(group)
```

**追問**:`permutations`(有序)vs `combinations`(無序);無限工具配 `islice`/`takewhile`;要 `list()` 才看內容。

---

## Q7. eager 和 lazy 求值差在哪?惰性有什麼實際應用與代價?

**考點**:惰性求值([07-lazy-evaluation](../chapters/07-iterators-generators/07-lazy-evaluation.md))

**答**:

- **eager(立即)**:馬上算、結果全佔記憶體(list 推導式)。
- **lazy(惰性)**:用到才算、記憶體恆定(生成器、`range`、`map`/`filter`/`zip`、itertools、檔案逐行)。

**關鍵應用**:**逐行迭代處理超大檔**(不整檔載入)、**串接生成器建零中間記憶體的管線**:

```python
with open("huge.log") as f:               # 檔案是惰性的
    errors = (line for line in f if "ERROR" in line)   # 惰性過濾
    count = sum(1 for _ in errors)         # 邊遍歷邊算,記憶體恆定
```

**代價**:一次性、無法索引/取長度、**副作用在遍歷時才發生**(而非定義時)。惰性管線**在遍歷前不執行**。

**追問**:`sum(gen)`/`max(gen)` 能邊遍歷邊算不必先 list;無限序列配 `islice`。

---

## Q8. 生成器怎麼變成協程?`send()` 做什麼?

**考點**:生成器協程([08-generator-as-coroutine](../chapters/07-iterators-generators/08-generator-as-coroutine.md))

**答**:`yield` 是**雙向的**——`yield x` **產出**值,`x = yield` **接收**值(配 `send()`)。這讓生成器成為**協程**(能被送入資料):

```python
def accumulator():
    total = 0
    while True:
        x = yield total    # 產出 total,同時接收送入的 x
        total += x

acc = accumulator()
next(acc)              # priming(必須先推進到第一個 yield)
acc.send(10)           # 送 10,回 10
acc.send(5)            # 送 5,回 15
```

三個控制方法:**`send()`**(送值 + 推進)、**`throw()`**(拋入例外)、**`close()`**(拋 `GeneratorExit` 清理)。

**追問**:

- **為什麼要先 priming?** → 生成器一開始停在函式開頭,必須先 `next()`/`send(None)` 推進到第一個 `yield`,才能 send,否則 TypeError。
- **和 asyncio 的關係?** → generator 協程是 **asyncio 的歷史前身**,`yield from` 是 `await` 前身;今天用 `async def`/`await`,但**底層暫停/恢復機制相同**。

---

⬅️ [Part 06](part06-error-handling.md) ｜ [索引](README.md) ｜ ➡️ [Part 08 函數式與裝飾器](part08-functional-decorators.md)
