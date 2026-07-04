# Part 09 面試題:並發與並行(GIL / asyncio)

> 對應 [Part 09 並發](../chapters/09-concurrency/README.md)。**Python 面試最大的重點區**——GIL、競態條件、asyncio、選型決策幾乎必考,答得好代表你真懂 Python。

---

## Q1. 並發和並行差在哪?I/O 密集和 CPU 密集各該用什麼?

**考點**:並發 vs 並行([01-concurrency-vs-parallelism](../chapters/09-concurrency/01-concurrency-vs-parallelism.md))

**答**:

- **並發(concurrency)**:**結構**上「處理多件事」——可在單核**交錯**進行(Rob Pike:「concurrency is about dealing with lots of things at once」)。
- **並行(parallelism)**:**執行**上「同時做」——需**多核**真正同時跑。

選工具看負載:

| 負載 | 特性 | 工具 |
|------|------|------|
| **I/O 密集** | 大部分時間在**等**(網路/磁碟) | threading / **asyncio** |
| **CPU 密集** | 大部分時間在**算** | **multiprocessing** |

**關鍵**:**GIL 讓 Python 執行緒無法並行 CPU 運算,但 I/O 等待時會釋放 GIL,所以能加速 I/O**——這是選工具的核心理由。CPU 密集也可向量化(numpy)/C 擴充。

---

## Q2.(必考)什麼是 GIL?為什麼存在?對多執行緒有什麼影響?

**考點**:GIL([02-gil](../chapters/09-concurrency/02-gil.md))

**答**:**GIL(Global Interpreter Lock)** 是 CPython 的一把鎖,保證**同一時刻只有一個執行緒執行 Python bytecode**。它是**實作細節**(CPython),非語言規範。

**為何存在**:保護**引用計數**等直譯器內部狀態、簡化記憶體管理、加快單執行緒、方便 C 擴充——是取捨。

**對多執行緒的影響(核心)**:

- **CPU 密集**:多執行緒**無法並行**(只能輪流跑 bytecode + 切換開銷),**不會變快、甚至更慢**。
- **I/O 密集**:**有效**——執行緒在 **I/O 等待時釋放 GIL**(還有每 ~5ms 定期釋放),讓別的執行緒跑。

**追問**:

- **怎麼繞過 GIL?** → `multiprocessing`(各行程獨立 GIL)、C 擴充/向量化(在 C 層釋放 GIL)、**free-threaded Python(3.13+)**(見 Q13)。
- **為何不直接拿掉 GIL?** → 會傷單執行緒效能、破壞 C 擴充相容性(PEP 703 正在解)。

---

## Q3.(必考)`counter += 1` 在多執行緒為什麼會丟失計數?有 GIL 也要鎖嗎?

**考點**:競態條件([03-threading](../chapters/09-concurrency/03-threading.md))

**答**:`counter += 1` **不是原子操作**——它是「讀取 → 加一 → 寫回」多條 bytecode,執行緒**可能在中間被切換**。兩個執行緒都讀到同一個舊值、各自加一寫回,就**丟失一次計數**(競態條件 race condition)。

**有 GIL 也要鎖!** GIL 只保證「同一時刻一條 bytecode」,但 `+=` 是**多條** bytecode,中間可被切換,所以仍需鎖:

```python
lock = threading.Lock()
def increment():
    with lock:           # 保護臨界區
        global counter
        counter += 1
```

**追問**:

- **怎麼用 threading?** → `Thread(target=f)` → `start()`(非同步啟動)→ `join()`(等待完成)。
- **daemon 執行緒?** → 隨主程式結束而終止,不保證清理。實務優先用 `ThreadPoolExecutor`。

---

## Q4. 執行緒同步有哪些工具?怎麼避免死鎖?

**考點**:同步原語([04-thread-sync](../chapters/09-concurrency/04-thread-sync.md))

**答**:

- **`Lock`**:互斥保護臨界區(`with lock:`,臨界區要小)。
- **`Event`**:訊號通知(set/wait/clear,優雅停止)。
- **`Semaphore`**:限制並發數。
- **`queue.Queue`**:執行緒安全的資料交換。

**推薦模式**:優先用 **`queue.Queue`「傳遞而非共享」**(生產者-消費者)——從根本避免競態,不必手動加鎖。

**死鎖**(高頻):成因是**多把鎖 + 不同取得順序 + 互相等待**(A 持鎖1 等鎖2、B 持鎖2 等鎖1)。避免:**固定取得順序**、用 `timeout`、減少鎖。

**追問**:「傳遞而非共享」為什麼好? → Queue 內部已處理同步,把「共享可變狀態」變成「傳訊息」,消除大部分競態。

---

## Q5.(必考)`multiprocessing` 和 threading 差在哪?為什麼要 `if __name__ == "__main__":`?

**考點**:multiprocessing([05-multiprocessing](../chapters/09-concurrency/05-multiprocessing.md))

**答**:**行程 vs 執行緒**:

| | 執行緒 | 行程 |
|---|--------|------|
| 記憶體 | 共享 | **獨立** |
| GIL | 共用一把 | **各自獨立 → 真正並行** |
| 資料傳遞 | 直接共享 | 要 **pickle 序列化** |
| 建立成本 | 輕 | 重 |
| 適合 | I/O 密集 | **CPU 密集** |

行程獨立 GIL,所以 **CPU 密集用 multiprocessing 繞過 GIL**。

**`if __name__ == "__main__":` 是必考陷阱**:Windows/macOS 用 **spawn** 建子行程時,子行程會**重新 import 主模組**——若建立行程的程式碼在頂層(沒被 `__main__` 保護),子行程 import 時又會**遞迴建立行程**(無限爆炸)。

**追問**:**不能傳 lambda**(pickle 限制),要用模組層級函式或 `partial`。有開銷(序列化 + 行程建立),只對「計算重、資料少」划算。實務用 `ProcessPoolExecutor`。

---

## Q6. `concurrent.futures` 有什麼價值?`Future` 是什麼?

**考點**:concurrent.futures([06-concurrent-futures](../chapters/09-concurrency/06-concurrent-futures.md))

**答**:`concurrent.futures` **統一了執行緒池(`ThreadPoolExecutor`/I/O)和行程池(`ProcessPoolExecutor`/CPU)** 的介面——**切換只需改類別名**(這是最大價值):

```python
from concurrent.futures import ThreadPoolExecutor  # I/O
# from concurrent.futures import ProcessPoolExecutor  # CPU,只改這行
with ThreadPoolExecutor() as ex:
    results = list(ex.map(fetch, urls))
```

**`Future`** 代表未來的結果:`.result()`(阻塞取結果/重拋例外)、`.done()`、`.exception()`、`.cancel()`。

**追問**:

- **`map` vs `as_completed` vs `submit`?** → `map` 依**輸入序**回結果;`as_completed` 依**完成序**;`submit` 最靈活(回 Future)。
- **陷阱?** → **Future 的例外要主動取(`.result()`),否則被吞掉**。

---

## Q7.(必考)什麼是 event loop?asyncio 和 threading 的多工模型差在哪?

**考點**:asyncio 基礎([07-asyncio-basics](../chapters/09-concurrency/07-asyncio-basics.md))

**答**:**event loop** 是單執行緒的排程器。協程在 **`await` 點主動讓出**控制權,event loop 就去跑別的就緒協程——這是**協作式多工(cooperative)**,與 threading 的**搶佔式(preemptive,OS 隨時切換)** 不同。

asyncio 適合**大量 I/O 並發**:單執行緒、無執行緒開銷、幾乎無競態/鎖(協作式,只在 await 點切換)。

**關鍵考點**:

```python
await a()    # 序列!等 a 完成才 b
await b()

results = await asyncio.gather(a(), b())   # 並發!同時跑
```

**追問**:呼叫 async 函式**回傳協程物件(不執行)**,要 await 或交給 loop;`asyncio.run` 是進入點。**一個阻塞操作會卡住整個 event loop**(見 Q11),要一路 async 到底。asyncio 不適合 CPU 密集(單執行緒)。

---

## Q8. `async def` 和 `await` 的語意?什麼是「函式染色」?

**考點**:async/await([08-async-await](../chapters/09-concurrency/08-async-await.md))

**答**:

- **`async def`**:定義**協程函式**,呼叫它**回傳協程物件、不執行**。
- **`await`**:只能在 async 函式裡用,**等待 awaitable 並讓出控制權**。awaitable 有三種:協程、Task、Future。

**函式染色(傳染性)**:要 `await` 一個東西,你的函式就必須是 `async`;這一路**傳染**到 `asyncio.run` 的邊界——「async 會傳染」。

**追問**:

- **"coroutine was never awaited" 警告?** → 呼叫了協程函式但**忘了 await**(協程物件沒被執行)。
- **例外?** → 透過 await **自然傳播**(try/except 照常用)。要用 **async 版函式庫**(如 `aiohttp` 而非 `requests`)。`async with`/`async for` 管理非同步資源/串流。

---

## Q9. `await coro` 和 `asyncio.gather` / `create_task` 差在哪?

**考點**:asyncio tasks([09-asyncio-tasks](../chapters/09-concurrency/09-asyncio-tasks.md))

**答**:

- **`await coro`**:**序列**——等這個完成才做下一個。
- **`create_task(coro)` / `gather(...)`**:**並發**——`create_task` 立刻排程、`gather` 同時跑一批並收集結果(依輸入序)。

```python
# 序列:總時間 = 三個之和
for url in urls: await fetch(url)
# 並發:總時間 ≈ 最慢那個
await asyncio.gather(*[fetch(u) for u in urls])
```

**追問**:

- **`gather(..., return_exceptions=True)`?** → 讓例外**當結果回傳**(不中斷其他 task)。
- **其他工具?** → `wait_for`(逾時)、`Task.cancel()`(取消,拋 `CancelledError`)、`Semaphore`(限流)。Task 要**保留參考**(否則可能被 GC)、外部呼叫設逾時、大量並發要限流。3.11+ 推薦 **TaskGroup**(見 Q10)。

---

## Q10. `TaskGroup`(3.11+)比 `gather` 好在哪?

**考點**:asyncio 進階([10-asyncio-advanced](../chapters/09-concurrency/10-asyncio-advanced.md))

**答**:`TaskGroup` = **結構化並發**:

- 任務生命週期**綁在 `async with` 區塊**,離開時全部完成。
- **任一失敗自動取消其餘**(gather 預設不會)。
- 錯誤打包成 **`ExceptionGroup`**(用 `except*` 處理,見 [Part 06](part06-error-handling.md#q9exceptiongroup-和-except-是什麼什麼時候用))。

```python
async with asyncio.TaskGroup() as tg:
    tg.create_task(a())
    tg.create_task(b())   # 任一失敗,另一個自動取消
```

**追問**:`async with`(`__aenter__`/`__aexit__`)非同步資源;`async for`(`__anext__`)+ async generator 非同步串流;用 **`asyncio.Lock`/`Semaphore`** 而非 threading 版(後者會阻塞 loop)。

---

## Q11.(必考)在 async 函式裡呼叫 `time.sleep(5)` 或 `requests.get` 會怎樣?

**考點**:阻塞卡 loop([11-blocking-in-async](../chapters/09-concurrency/11-blocking-in-async.md))

**答**:**凍結整個 event loop**!asyncio 是**單執行緒**,一個同步阻塞操作(`time.sleep`、`requests.get`、重 CPU 運算)會**霸佔執行緒**,所有其他協程全部卡死。

**解法**:把阻塞工作丟出去:

- **阻塞 I/O → 執行緒池**:`await asyncio.to_thread(blocking_io)`(3.9+,最簡單)。
- **CPU 密集 → 行程池**:`loop.run_in_executor(ProcessPoolExecutor(), cpu_work)`。
- **協程裡要等待用 `asyncio.sleep`**,不是 `time.sleep`。

```python
result = await asyncio.to_thread(requests.get, url)   # 橋接同步函式庫
```

**追問**:對應關係和 threading/multiprocessing 一樣(阻塞 I/O→執行緒、CPU→行程)。**優先用 async 原生函式庫**(aiohttp/asyncpg),`to_thread` 是橋接同步函式庫的權宜之計。

---

## Q12.(必考)給你這幾種情境,各該用哪種並發模型?

**考點**:選型決策([13-choosing-concurrency-model](../chapters/09-concurrency/13-choosing-concurrency-model.md))

**答**:決策準則:

| 情境 | 模型 | 理由 |
|------|------|------|
| **CPU 密集**(影像處理、數值計算) | **multiprocessing** | 繞過 GIL 真並行 |
| **少量 I/O**(幾個檔案/請求) | **threading** | 簡單、等待釋放 GIL |
| **大量 I/O**(幾千連線) | **asyncio** | 單執行緒省開銷、擴展性好 |
| 數值運算 | **向量化(numpy)** | C 層釋放 GIL、更快 |

**選錯的後果**:CPU 用 threading **無效**(GIL);輕量 I/O 用 process **浪費**(建立開銷);海量連線用 thread **撐不住**(每執行緒 ~MB 記憶體);asyncio 裡放阻塞**卡 loop**。

**追問**:混合負載可組合(asyncio 主 + 行程池處理 CPU + `to_thread` 橋接阻塞);實務用 `concurrent.futures` 統一介面。**先量測、能不並發就不並發**(並發增加複雜度)。

---

## Q13. free-threaded Python 是什麼?現在能用嗎?

**考點**:無 GIL Python([12-free-threaded-python](../chapters/09-concurrency/12-free-threaded-python.md))

**答**:**PEP 703 / free-threaded Python**——**3.13 起提供可選的實驗性無 GIL 建置**,讓執行緒能**真正並行 CPU 運算 + 保留共享記憶體**,解決 Python 並發最大痛點(不必再靠 multiprocessing 的序列化開銷)。

**關鍵**:它是**實驗性、不是預設**(標準 3.13 仍有 GIL)。**取捨**:單執行緒可能變慢、需要 C 擴充相容——這正是歷史上移除 GIL 困難的原因。

**追問**:

- **若普及的影響?** → CPU 密集可直接用 threading(免去 multiprocessing 的 pickle/行程開銷)。
- **現在該怎麼辦?** → 正式專案仍用既有策略(Q12),**關注但不依賴**。這是近年最熱門的 Python 並發面試話題,能談代表你跟上生態演進。

---

⬅️ [Part 08](part08-functional-decorators.md) ｜ [索引](README.md) ｜ ➡️ [Part 10 CPython 內部](part10-cpython-internals.md)
