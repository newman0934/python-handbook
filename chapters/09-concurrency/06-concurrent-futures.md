# concurrent.futures

> `concurrent.futures` 用同一套 API 統一了執行緒池與行程池——`ThreadPoolExecutor`（I/O）和 `ProcessPoolExecutor`（CPU）。它比手動管理 Thread/Process 簡潔太多，是實務上多數並發任務的首選。

## Why（為什麼）

前面手動建立 Thread/Process 又要 `start`、`join`、還要自己收集結果與例外，繁瑣易錯。`concurrent.futures` 提供**高階、統一**的介面：建一個「執行器（Executor）」、丟工作進去、拿回 `Future`（代表未來的結果）。最棒的是——**切換執行緒池和行程池只要改一個類別名**（`ThreadPoolExecutor` ↔ `ProcessPoolExecutor`）。這是實務上做並發的推薦工具，比裸 threading/multiprocessing 好用得多。

## Theory（理論：Executor 與 Future）

兩個核心概念：

- **Executor（執行器）**：管理一個「工作者池」（執行緒或行程），你把工作丟進去，它負責調度。兩種：
  - **`ThreadPoolExecutor`**：執行緒池 → **I/O 密集**。
  - **`ProcessPoolExecutor`**：行程池 → **CPU 密集**（繞過 GIL）。
- **Future（未來物件）**：代表「一個尚未完成的工作的結果」——你提交工作後立刻拿到一個 Future，之後可以 `.result()` 取結果（阻塞直到完成）或查詢狀態。

統一 API 的價值：**同樣的程式碼，換個 Executor 就從執行緒切換到行程**——先判斷 I/O 還是 CPU 密集（見 [並發 vs 並行](01-concurrency-vs-parallelism.md)），選對應的 Executor 即可。

## Specification（規範：兩種提交方式）

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

# map：像內建 map，但平行執行，回傳結果（依輸入順序）
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(func, iterable))    # 平行套用

# submit + Future：更靈活，可個別處理
with ThreadPoolExecutor() as executor:
    future = executor.submit(func, arg)    # 提交，回傳 Future
    result = future.result()               # 取結果（阻塞直到完成）

# submit 多個 + as_completed：誰先完成先處理
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(func, x) for x in data]
    for future in as_completed(futures):   # 依「完成順序」產出
        print(future.result())

# CPU 密集只需換類別
with ProcessPoolExecutor() as executor:    # 同樣的 API！
    results = list(executor.map(cpu_func, data))
```

## Implementation（map、submit、as_completed、例外、切換）

### `map`：最簡單，依序取結果

```python
from concurrent.futures import ThreadPoolExecutor
import time

def fetch(url: str) -> str:
    time.sleep(0.3)          # 模擬 I/O
    return f"{url} 的內容"

urls = ["a.com", "b.com", "c.com"]
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(fetch, urls))    # 平行下載，約 0.3s
# results 依「輸入順序」（不是完成順序）
```

`executor.map` 像內建 `map` 但平行執行，結果**依輸入順序**回傳。適合「一批同構工作、要對應順序的結果」。`with` 區塊結束會自動等所有工作完成並關閉池。

### `submit` + `Future`：更靈活

`submit` 回傳 `Future`，讓你能個別控制、非同步取結果、處理例外：

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor() as executor:
    future = executor.submit(fetch, "a.com")
    # ... 可以做別的事 ...
    print(future.done())        # 查詢是否完成
    result = future.result()    # 取結果（阻塞直到完成）
    result = future.result(timeout=5)   # 可設逾時
```

`Future` 的方法：`.result()`（取結果/阻塞）、`.done()`（是否完成）、`.exception()`（取例外）、`.cancel()`（嘗試取消）。

### `as_completed`：誰先完成先處理

當你不在乎順序、想「誰先好就先處理誰」（如即時顯示進度），用 `as_completed`：

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor() as executor:
    futures = {executor.submit(fetch, url): url for url in urls}
    for future in as_completed(futures):     # 依完成順序
        url = futures[future]
        print(f"{url} 完成: {future.result()}")
```

`as_completed` 依**完成順序**產出 Future（快的先出），適合「即時處理結果」的場景。

### 例外處理：`Future` 捕捉例外

工作裡拋的例外**不會**立刻炸——它被存在 Future 裡，直到你 `.result()` 才重新拋出：

```python
with ThreadPoolExecutor() as executor:
    future = executor.submit(risky_task)
    try:
        result = future.result()     # 若 risky_task 拋例外，這裡重新拋出
    except ValueError as e:
        print(f"任務失敗: {e}")
```

用 `executor.map` 時，例外在你迭代到那個結果時拋出。**別忘了處理 Future 的例外**——否則失敗會被默默吞掉（尤其只 submit 不取 result 時）。

### 切換執行緒 ↔ 行程：一行之差

```python
# I/O 密集
from concurrent.futures import ThreadPoolExecutor as Executor
# CPU 密集：只改這行
from concurrent.futures import ProcessPoolExecutor as Executor

with Executor() as executor:
    results = list(executor.map(task, data))    # 其餘完全相同
```

這是 `concurrent.futures` 最大的價值——**統一 API 讓你能輕鬆切換並發策略**，先判斷任務類型再選 Executor（ProcessPoolExecutor 一樣需注意 `if __name__ == "__main__"` 與 pickle 限制，見 [multiprocessing](05-multiprocessing.md)）。

## Code Example（可執行的 Python 範例）

```python
# concurrent_futures_demo.py
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def io_task(name: str, duration: float) -> str:
    time.sleep(duration)
    return f"{name} 完成（{duration}s）"


def demo() -> None:
    tasks = [("A", 0.3), ("B", 0.2), ("C", 0.1)]

    # 1. map：依輸入順序
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda t: io_task(*t), tasks))
    print(f"map 結果（依輸入序）: {results}")
    print(f"耗時: {time.perf_counter() - start:.2f}s（並發約 0.3s）")

    # 2. as_completed：依完成順序（C 最快先出）
    print("\nas_completed（依完成序）:")
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(io_task, name, dur): name for name, dur in tasks}
        for future in as_completed(futures):
            print(f"  {future.result()}")

    # 3. Future 例外處理
    def failing() -> str:
        raise ValueError("模擬失敗")

    with ThreadPoolExecutor() as executor:
        future = executor.submit(failing)
        try:
            future.result()
        except ValueError as e:
            print(f"\n捕捉到工作例外: {e}")


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python concurrent_futures_demo.py
map 結果（依輸入序）: ['A 完成（0.3s）', 'B 完成（0.2s）', 'C 完成（0.1s）']
耗時: 0.30s（並發約 0.3s）

as_completed（依完成序）:
  C 完成（0.1s）
  B 完成（0.2s）
  A 完成（0.3s）

捕捉到工作例外: 模擬失敗
```

## Diagram（圖解：Executor 與 Future）

```mermaid
flowchart TD
    A["submit(func, arg)"] --> B[Executor 池調度]
    A --> F["立刻回傳 Future"]
    B --> W["工作者(執行緒/行程)執行"]
    W --> R[結果/例外存進 Future]
    F -->|.result()| R
    F -->|.done()/.exception()| R
    style F fill:#e8f5e9
```

## Best Practice（最佳實踐）

- **實務並發首選 `concurrent.futures`**：比手動 Thread/Process 簡潔、統一、易取結果與例外。
- **先判斷任務類型選 Executor**：I/O 密集用 `ThreadPoolExecutor`、CPU 密集用 `ProcessPoolExecutor`（一行之差）。
- **用 `with` 管理 Executor**：自動等待完成並清理資源。
- **簡單批次用 `map`（依輸入序）**；要即時處理用 `as_completed`（依完成序）；要靈活控制用 `submit` + Future。
- **一定處理 Future 的例外**（`.result()` 會重拋，或用 `.exception()`），別讓失敗被吞掉。
- **設合理的 `max_workers`**：I/O 可較多、CPU 通常設為核心數（`os.cpu_count()`）；預設值多數情況夠用。
- **ProcessPoolExecutor 遵守 multiprocessing 規則**：`if __name__ == "__main__"`、函式可 pickle（見 [multiprocessing](05-multiprocessing.md)）。

## Common Mistakes（常見誤解）

- **只 `submit` 不取 `.result()`**：工作裡的例外被默默吞掉，失敗無感知。
- **選錯 Executor**：I/O 用 Process（浪費）、CPU 用 Thread（GIL 無效）。
- **不用 `with` 管理**：忘了 shutdown，資源沒釋放。
- **`map` 期待依完成順序**：它依**輸入順序**；要完成順序用 `as_completed`。
- **ProcessPoolExecutor 傳 lambda**：pickle 限制，用具名函式。
- **`max_workers` 設太大**：太多執行緒/行程反而有開銷與資源耗盡。
- **在工作函式裡不處理例外，也不在 result 端處理**：失敗靜默。

## Interview Notes（面試重點）

- 知道 **`concurrent.futures` 統一了執行緒池（ThreadPoolExecutor / I/O）與行程池（ProcessPoolExecutor / CPU）**，**切換只需改類別名**——這是它最大價值。
- 知道 **`Future`** 代表未來結果：`.result()`（阻塞取結果/重拋例外）、`.done()`、`.exception()`、`.cancel()`。
- **能對比 `map`（依輸入序）vs `as_completed`（依完成序）vs `submit`（靈活）**。
- 知道 **Future 的例外要主動取（`.result()`）否則被吞掉**。
- 知道實務上優先用它而非裸 threading/multiprocessing，且 ProcessPoolExecutor 遵守 multiprocessing 的 `__main__`/pickle 規則。

---

➡️ 下一章：[asyncio 基礎與 event loop](07-asyncio-basics.md)

[⬆️ 回 Part 9 索引](README.md)
