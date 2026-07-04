# Part 18 面試題:效能優化

> 對應 [Part 18 效能](../chapters/18-performance/README.md)。核心:先量測別猜、複雜度金字塔、快取、Cython/numba、`__slots__`。

---

## Q1. 怎麼做效能優化?為什麼「別猜」?

**考點**:profiling([01-profiling](../chapters/18-performance/01-profiling.md))

**答**:**先量測、別猜**——「過早優化是萬惡之源」。優化循環:**量測 → 定位熱點 → 優化 → 再量測驗證**。依 **80/20 法則**,少數程式碼佔多數時間,優化非瓶頸是白費。

工具:**`cProfile`** 是**確定性 profiler**(看得到 `ncalls`,但 per-call 有開銷,絕對值偏慢、相對比例可靠)。

**追問**:

- **`tottime` vs `cumtime`?** → `tottime`(函式**自身**耗時,找熱點運算);`cumtime`(**累積**含子函式,找貴的呼叫鏈)。
- **確定性 vs 取樣?** → 正式環境用**取樣 profiler**(py-spy/scalene,低開銷)。函式級(cProfile)→ 行級(line_profiler)漸進定位。

---

## Q2. 為什麼不能用 `time.time()` 量小程式碼?`timeit` 為什麼取 min?

**考點**:timeit([02-timeit](../chapters/18-performance/02-timeit.md))

**答**:`time.time()` **解析度不夠**(量微秒級不準)、**受雜訊干擾**、含一次性成本(import/快取)。`timeit` 解決:用 `perf_counter`、`number` 放大重複次數、`repeat` 多輪取 **min**、隔離 setup。

**取 min 而非 mean**:干擾(OS 排程、GC)**只會讓程式變慢**,所以**最小值最接近真實成本**(沒被干擾的那次)。

**追問**:`timeit`(微基準/寫法比較)vs `cProfile`(找整體熱點);timeit 預設關 GC;經典結論:`''.join` 比 `+=`(O(n²))快、`set` 的 `in` 比 `list` 快(O(1) vs O(n))。**微基準的侷限**:局部結論不等於整體,要結合 profiling。

---

## Q3.(必考)優化的優先順序?哪些操作是 O(1)、哪些是 O(n)?

**考點**:優化策略([03-optimization-strategies](../chapters/18-performance/03-optimization-strategies.md))

**答**:**優化金字塔**(先從上層下手,複雜度主導大局):

```text
演算法 > 資料結構 > 內建/C > 微優化
```

換個 O(n log n) 演算法勝過微優化 O(n²) 迴圈。

**關鍵複雜度**:

| 操作 | 複雜度 |
|------|--------|
| `x in list` / `list.pop(0)` | **O(n)** |
| `x in set` / `x in dict` / dict 查找 | **O(1)**(雜湊表) |
| `deque` 兩端操作 | O(1) |

**經典陷阱**:**O(n) 操作放進迴圈 = O(n²)**:

```python
result = []
for x in items:
    if x not in result:      # O(n) 在迴圈裡 → O(n²)!
        result.append(x)
# 用 set:O(n)
seen = set(); result = [x for x in items if not (x in seen or seen.add(x))]
```

**追問**:內建函式比手寫迴圈快(C 層迴圈、省直譯開銷),但**複雜度不變**;先 profiling 找熱點、可讀性優先。

---

## Q4. 快取(記憶化)怎麼加速?前提是什麼?

**考點**:快取([04-caching](../chapters/18-performance/04-caching.md))

**答**:記憶化把費氏遞迴從 **O(2ⁿ) 降到 O(n)**——**空間換時間**(存過的結果不重算):

```python
@functools.lru_cache(maxsize=None)
def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)
```

**前提:純函式**(確定性、無副作用)——快取不純函式會給錯結果。

**追問**:

- **快取失效?** → 「cache invalidation 是最難的問題之一」——資料變動時如何讓快取一致(見 [Part 15 Redis](part15-database.md#q7-redis-為什麼快cache-aside-模式快取三大問題))。
- **監控?** → `cache_info()` 讀 hits/misses;`cache_clear()` 失效;`@cache`(3.9+)、`cached_property`;**方法上快取持有 `self` 有洩漏風險**。

---

## Q5. Python 為什麼慢?Cython 和 numba 怎麼加速?

**考點**:Cython/numba([05-cython-numba](../chapters/18-performance/05-cython-numba.md))

**答**:Python 慢的根源:**動態型別 + 物件拆裝箱 + 直譯開銷**,數值迴圈尤其吃虧。

- **Cython(AOT)**:加型別註記 → 提前編譯成 C。
- **numba(JIT)**:`@njit` 執行時把數值函式編成機器碼。

兩者都**確定型別 → 生成原生機器碼 → 繞過直譯器與拆裝箱**,且**可釋放 GIL**(數值運算多核,純 Python 做不到)。

**選型**:**先 numpy 向量化 → 難向量化用 numba → 要套件化/整合 C 用 Cython**。**這是最後手段**——先 profiling、先解演算法/資料結構、先試向量化,數值熱點才編譯。

**追問**:numba 首次呼叫含編譯成本;`@njit` 的 nopython 模式(完全不回退到 Python 才快)。

---

## Q6. `__slots__` 為什麼省記憶體?有什麼代價?

**考點**:記憶體優化([06-memory-optimization](../chapters/18-performance/06-memory-optimization.md))

**答**:`__slots__` **拿掉 per-instance `__dict__`**——屬性改存類別配置的**固定槽位**(descriptor),省去 dict 的 hash 結構與預留空間(大量實例時省很多):

```python
class Point:
    __slots__ = ("x", "y")     # 沒有 __dict__
```

**代價**:不能動態加屬性、子類別需自行宣告才保留節省、預設無弱引用。

**追問**:`sys.getsizeof` 只算**淺層**大小(不含 `__dict__`/內容),量大範圍用 `tracemalloc`;生成器 vs list 的記憶體差異(惰性、常數記憶體 vs 全載入);`@dataclass(slots=True)`;**大量實例才值得用 slots**,先量測。

---

## Q7. async 加速的是什麼?什麼情況 async 沒用?

**考點**:async 效能([07-async-performance](../chapters/18-performance/07-async-performance.md))

**答**:async 加速的是 **I/O-bound**——單執行緒事件迴圈**重疊等待**(`await` 讓出、OS I/O 多工),**不是平行計算**。所以:

- **I/O-bound**(網路/DB)→ async/執行緒:等待時去做別的。
- **CPU-bound**(計算)→ **async 無效**(無 `await` 讓出點會霸佔迴圈,且 GIL 限制)→ 用多行程。

最大陷阱:**事件迴圈裡的阻塞呼叫**(卡住所有請求,見 [Part 09/14](part14-web.md#q9必考在-async-def-端點裡放阻塞操作會怎樣)),解法:async 函式庫 / `to_thread` / 多行程。

**追問**:`gather`/`TaskGroup` 併發、`Semaphore` 限流、`timeout` 逾時;循序疊加 vs 併發重疊的差異(換成阻塞 sleep 就退化成循序)。

---

⬅️ [Part 17](part17-data-science.md) ｜ [索引](README.md) ｜ ➡️ [Part 19 雲原生與部署](part19-cloud-native.md)
