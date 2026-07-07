# generator 當協程：send / throw / close

> 生成器不只能「產出」值，還能「接收」值——`yield` 可以是運算式，用 `send()` 把值送進去。這讓生成器變成雙向溝通的協程，是理解 asyncio 底層與 `await` 起源的鑰匙。

## 💡 白話導讀（建議先讀）

目前為止，生成器像**廣播電台**——只出不進：yield 把值播出去，外面只能聽。

這章解鎖隱藏功能：**yield 其實是對講機**——不只能喊話，還能**收話**：

```python
def machine():
    while True:
        cmd = yield "待命中"     # ← yield 出現在等號右邊!
        print(f"收到指令:{cmd}")  #    停在這裡「等外面說話」
```

讀法變了：`x = yield v` 是「**播出 v,然後停下來等——外面送什麼進來,就賦給 x**」。

外面怎麼送？用 `send()`：

```python
m = machine()
next(m)              # 先「暖機」推進到第一個 yield(必要步驟,常忘)
m.send("開工")        # 送話進去 → 裡面的 cmd = "開工",跑到下一個 yield
```

能收話的生成器有了新身分——**協程（coroutine）**：一個可以暫停、等待輸入、被逐步推進的執行單位。

搭配的還有兩個控制鍵：`throw()`（對著對講機丟例外進去）、`close()`（請它收工）。

老實說：**日常你幾乎不會手寫這種程式碼**。學它的價值是**考古**——這套「暫停、等待、送值恢復」的機制,正是 [asyncio 與 async/await](../09-concurrency/07-asyncio-basics.md) 的前身:`await` 本質上就是這裡的機制加上語法糖。懂了對講機,event loop 就不再是魔法。

## Why（為什麼）

到目前為止，生成器都是「單向」的：只吐值出來（`yield x`）。但 `yield` 還有另一面——它可以**當運算式接收外部送進來的值**（`x = yield`）。加上 `send()`、`throw()`、`close()` 三個方法，生成器就成了能雙向溝通、可被外部控制的**協程（coroutine）**。這是理解 asyncio 底層機制、以及 `yield from`/`await` 歷史演進的關鍵。雖然日常寫 async 你會用 `async def`，但懂這層能讓你真正理解「協程」是什麼。

## Theory（理論：yield 的雙向性）

`yield` 有兩個方向——廣播與對講：

- **產出（output）**：`yield value` 把 value 送給外部（`next()`/`for` 取得）——廣播。
- **接收（input）**：`x = yield` 讓生成器**暫停並等待**，外部用 `send(v)` 送值進來，`v` 成為 `yield` 運算式的值（賦給 `x`）——對講機收話。

用上「接收」這一面，生成器就從「產出序列的 iterator」升級為「能接收外部輸入、逐步推進的**協程**」。

三個控制方法：

- **`gen.send(value)`**：送值進生成器（`yield` 運算式回傳該值），並推進到下個 `yield`。
- **`gen.throw(exc)`**：在生成器暫停處拋入一個例外。
- **`gen.close()`**：在暫停處拋入 `GeneratorExit`，請生成器收尾。

這套「暫停、等待、送值恢復」正是 asyncio 與 `await` 的機制前身。

## Specification（規範：協程的啟動與溝通）

```python
def coroutine():
    while True:
        received = yield          # 暫停，等待 send() 送值進來
        print(f"收到: {received}")

co = coroutine()
next(co)              # 必須先「啟動」（推進到第一個 yield）——這步叫 priming
# 或 co.send(None)    # 等價於 next(co)
co.send("hello")      # 收到: hello
co.send("world")      # 收到: world
co.close()            # 結束協程
```

## Implementation（priming、send、close、與 async 的關係）

### 必須先「啟動」（priming）

以接收為主的協程，**第一次必須先 `next(co)` 或 `co.send(None)`** 把它推進到第一個 `yield`（暫停在等待處），才能開始 `send` 值。這步叫 **priming（預激）**：

```python
co = coroutine()
# co.send("x")        # ❌ 錯誤：還沒啟動就 send → TypeError
next(co)              # ✅ 先 priming，推進到第一個 yield
co.send("x")          # 現在可以送值了
```

忘了 priming 是協程的經典錯誤（`TypeError: can't send non-None value to a just-started generator`）。

### 雙向溝通：既接收又產出

`yield` 可以同時做兩件事——`received = yield result`：先產出 `result`，暫停，再接收送進來的值：

```python
def accumulator():
    total = 0
    while True:
        value = yield total       # 產出目前總和，並接收下一個要加的值
        total += value

acc = accumulator()
next(acc)                 # priming，產出初始 0
print(acc.send(10))       # 送 10 進去，產出 10
print(acc.send(5))        # 送 5，產出 15
print(acc.send(3))        # 產出 18
```

這是「有記憶、可互動」的協程——每次 send 推進一步、回傳當前狀態。

### `close()` 與 `GeneratorExit`

`close()` 在暫停處拋入 `GeneratorExit`，讓協程做清理。可在 `finally` 或捕捉 `GeneratorExit` 中收尾：

```python
def worker():
    try:
        while True:
            task = yield
            print(f"處理 {task}")
    finally:
        print("清理資源")        # close() 時執行

w = worker()
next(w)
w.send("task1")
w.close()                  # 觸發 GeneratorExit → 印「清理資源」
```

### `throw()`：從外部拋入例外

`gen.throw(SomeError)` 在生成器暫停處拋入例外，生成器可以捕捉並處理——用於通知協程「發生了某狀況」。

### 與現代 async 的關係（重要脈絡）

這種「基於生成器的協程」是 **asyncio 的歷史前身**。早期（Python 3.4）用 `@asyncio.coroutine` + `yield from` 寫協程；3.5 引入 `async def`/`await` 語法（見 [async/await](../09-concurrency/08-async-await.md)），取代了這套。**今天寫非同步程式一律用 `async def`/`await`**，不用手寫 generator 協程。

但理解 generator 協程能讓你懂：`await` 本質就是「暫停當前協程、把控制權交回事件迴圈、等結果回來再恢復」——和 `yield`/`send` 的暫停恢復是同一個機制。這是「知其所以然」的一章。

## Code Example（可執行的 Python 範例）

```python
# coroutine_demo.py
from __future__ import annotations

from collections.abc import Generator


def running_average() -> Generator[float, float, None]:
    """協程：接收數值，產出目前的平均。"""
    total = 0.0
    count = 0
    average = 0.0
    while True:
        value = yield average       # 產出平均，接收下一個值
        total += value
        count += 1
        average = total / count


def logger(prefix: str) -> Generator[None, str, None]:
    """協程：接收訊息並記錄，close 時清理。"""
    logs: list[str] = []
    try:
        while True:
            msg = yield
            logs.append(f"{prefix}: {msg}")
    finally:
        print(f"關閉，共記錄 {len(logs)} 則: {logs}")


def demo() -> None:
    # 1. 運行平均協程
    avg = running_average()
    next(avg)                        # priming
    print(f"送 10 → 平均 {avg.send(10)}")     # 10.0
    print(f"送 20 → 平均 {avg.send(20)}")     # 15.0
    print(f"送 30 → 平均 {avg.send(30)}")     # 20.0

    # 2. 記錄協程 + close 清理
    log = logger("APP")
    next(log)                        # priming
    log.send("啟動")
    log.send("處理中")
    log.close()                      # 觸發 finally 清理


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python coroutine_demo.py
送 10 → 平均 10.0
送 20 → 平均 15.0
送 30 → 平均 20.0
關閉，共記錄 2 則: ['APP: 啟動', 'APP: 處理中']
```

## Diagram（圖解：send 的雙向溝通）

```mermaid
flowchart TD
    A["next(co) / send(None): priming"] --> B["協程暫停於 x = yield result"]
    B -->|外部 send(v)| C["v 賦給 x, 恢復執行"]
    C --> D[執行到下個 yield]
    D --> E["產出新 result, 再暫停"]
    E -->|再 send| C
    F["close()"] --> G["拋入 GeneratorExit → finally 清理"]
    style C fill:#e8f5e9
    style G fill:#fff3e0
```

## Best Practice（最佳實踐）

- **今天寫非同步一律用 `async def`/`await`**（見 [async/await](../09-concurrency/08-async-await.md)），別手寫 generator 協程——後者是歷史/底層知識。
- **理解 generator 協程是為了懂 `await` 的本質**（暫停/恢復、把控制權交出去）。
- **若真的用 generator 協程**：記得先 **priming**（`next()`/`send(None)`）再 send。
- **在 `finally` 做清理**，讓 `close()` 能正確收尾。
- **`Generator[Yield, Send, Return]` 型別註記**：三個參數分別是 yield 型別、send 型別、return 型別。
- **一般的「產出序列」用普通生成器就好**，別為了用 send 而複雜化。

## Common Mistakes（常見誤解）

- **忘了 priming 就 send**：`TypeError: can't send non-None value to a just-started generator`；先 `next()`/`send(None)`。
- **混淆 `yield` 的兩個方向**：`yield x`（產出）vs `x = yield`（接收）；`x = yield result` 兩者都做。
- **以為 generator 協程是現代 async 的寫法**：它是前身；今天用 `async def`/`await`。
- **`close()` 後繼續 send**：協程已結束，會 `StopIteration`。
- **不在 finally 清理**：`close()`/`GeneratorExit` 時資源沒釋放。
- **型別註記用錯**：`Generator[Y, S, R]` 三參數常被寫錯或只寫一個。
- **在協程裡吞掉 `GeneratorExit`**：捕捉後不重拋且繼續 yield 會 RuntimeError。

## Interview Notes（面試重點）

- 說得出 **`yield` 的雙向性**：`yield x` 產出、`x = yield` 接收（配 `send()`），使生成器成為**協程**。
- 知道 **`send()`（送值 + 推進）、`throw()`（拋入例外）、`close()`（GeneratorExit 清理）** 三個控制方法。
- **知道必須先 priming**（`next()`/`send(None)`）才能 send，否則 TypeError。
- **關鍵脈絡**：generator 協程是 **asyncio 的歷史前身**，`yield from` 是 `await` 的前身；今天用 `async def`/`await`，但底層的暫停/恢復機制相同。
- 知道 `Generator[Yield, Send, Return]` 型別註記與在 finally 清理的重要性。

---

🎉 **恭喜完成 Part 7！** 你已掌握 Python 的迭代與生成：iterable/iterator 協定、`__iter__`/`__next__`、生成器與 yield、生成器表達式、yield from、itertools、惰性求值與記憶體效益、以及生成器作為協程。
接下來 [Part 8 函數式與裝飾器](../08-functional-decorators/README.md) 將進入高階函式、decorator 與 functools。

[⬆️ 回 Part 7 索引](README.md)
