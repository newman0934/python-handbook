# Python 面試題庫索引

> 這是全書技術內容的**面試視角總索引**：把散落各章的核心考點，依主題彙整成一份「面試前複習清單」。每個考點附「面試官想聽到什麼」與深入章節連結，讓你能快速自我檢測、查漏補缺。

## Why（為什麼）

讀完整本書，你累積了大量知識——但面試前，你需要的是一份**濃縮的複習地圖**：哪些是高頻考點、每個考點「面試官想聽到的完整回答」是什麼、我哪裡還不熟。散落在 20 個 Part 裡的知識，這章幫你**依面試主題重新組織**，讓你能：

- **快速自我檢測**：對照清單，能流暢回答的打勾、卡住的回去重讀。
- **抓住重點**：面試考的往往是「為什麼」與「底層原理」，而非 API 用法——本書的深度正好對應。
- **建立回答框架**：每個考點知道「該講到哪些點」才算完整。

這章不重複教內容（那是各章的事），而是當**索引與檢核表**。真正的深度在連結的章節裡；這裡給你「面試官會問什麼、答案的骨架在哪」。搭配 [行為面試](14-behavioral-interview.md)，技術 + 軟實力兩手準備。更完整的題目與解答見專案的 `interview/` 題庫目錄。

## 核心考點索引（依主題）

### 語言核心與資料模型

- **「Python 一切皆物件是什麼意思？」** → 變數是名字綁定到物件、`is` vs `==`、`id()`。見 [物件模型](../10-cpython-internals/README.md)。
- **「可變 vs 不可變？為什麼重要？」** → list/dict 可變、tuple/str/int 不可變；預設參數陷阱、字典 key 需 hashable。見 [資料結構](../03-data-structures/README.md)。
- **「dict/set 為何 O(1)？」** → 雜湊表、hash 與 `__eq__`。見 [dict 底層](../03-data-structures/README.md)。
- **「LEGB 作用域與閉包？」** → Local/Enclosing/Global/Builtin、`nonlocal`、late binding 閉包陷阱。見 [作用域](../02-fundamentals/README.md)。
- **「深拷貝 vs 淺拷貝？」** → `copy` vs `deepcopy`、共享參照。見 [資料結構](../03-data-structures/README.md)。

### OOP 與型別

- **「MRO 與多重繼承？」** → C3 線性化、`super()`、菱形繼承。見 [MRO](../04-oop/README.md)。
- **「魔術方法？」** → `__init__`/`__repr__`/`__eq__`/`__hash__`/`__enter__` 等協定。見 [魔術方法](../04-oop/README.md)。
- **「`@property`/`@classmethod`/`@staticmethod` 差別？」** → descriptor、綁定。見 [OOP](../04-oop/README.md)。
- **「dataclass vs 一般 class？」** → 自動生成、`slots=True`、`frozen`。見 [dataclass](../04-oop/README.md)。
- **「type hint 有什麼用？執行期會檢查嗎？」** → 靜態檢查（mypy）、執行期不強制、Protocol/Generic。見 [型別系統](../05-typing/README.md)。

### 並發與 CPython 內部

- **「GIL 是什麼？如何影響並發？」** → 同一時刻一執行緒執行 bytecode；I/O-bound 用 threading/asyncio、CPU-bound 用 multiprocessing。見 [GIL](../09-concurrency/README.md)。
- **「threading vs multiprocessing vs asyncio 怎麼選？」** → I/O-bound vs CPU-bound、事件迴圈。見 [並發](../09-concurrency/README.md)、[非同步效能](../18-performance/07-async-performance.md)。
- **「asyncio 如何運作？async worker 裡能不能跑阻塞/CPU 密集？」** → 事件迴圈、`await` 讓出、阻塞會卡死迴圈。見 [asyncio](../09-concurrency/README.md)。
- **「Python 如何管理記憶體？」** → 引用計數 + 循環 GC、`sys.getrefcount`。見 [引用計數與 GC](../10-cpython-internals/README.md)。
- **「引用計數的循環參照問題？」** → 循環 GC 補足、`__del__` 注意事項。見 [GC](../10-cpython-internals/README.md)。

### 迭代器、生成器、裝飾器

- **「iterable vs iterator？」** → `__iter__`/`__next__`、`StopIteration`。見 [迭代器](../07-iterators-generators/README.md)。
- **「生成器與 yield？省什麼？」** → 惰性、常數記憶體、串流大資料。見 [生成器](../07-iterators-generators/README.md)、[記憶體優化](../18-performance/06-memory-optimization.md)。
- **「裝飾器原理？」** → 高階函式、`functools.wraps`、帶參數裝飾器。見 [裝飾器](../08-functional-decorators/README.md)。
- **「context manager / with？」** → `__enter__`/`__exit__`、`contextlib`。見 [context manager](../06-error-handling/README.md)。

### 測試、工程化、效能

- **「pytest fixture / mock / 參數化？」** → 依賴注入、`monkeypatch`、`parametrize`。見 [測試](../12-testing/README.md)。
- **「怎麼找效能瓶頸？」** → 先量測（cProfile）、tottime vs cumtime、80/20。見 [profiling](../18-performance/01-profiling.md)。
- **「怎麼優化 Python 程式？」** → 演算法 > 資料結構 > 內建 > 微優化；快取；向量化。見 [優化策略](../18-performance/03-optimization-strategies.md)。
- **「`__slots__` 有什麼用？」** → 省記憶體（去 `__dict__`）、限制屬性。見 [記憶體優化](../18-performance/06-memory-optimization.md)。

### Web、資料庫、架構

- **「WSGI vs ASGI？」** → 同步 vs 非同步、Gunicorn/Uvicorn。見 [Gunicorn/Uvicorn](../19-cloud-native/03-gunicorn-uvicorn.md)。
- **「N+1 查詢？怎麼解？」** → lazy loading、eager loading、`selectinload`。見 [N+1](../15-database/10-n-plus-1.md)。
- **「交易 ACID / 隔離級別？」** → 原子性、一致性、隔離、持久。見 [交易](../15-database/06-transactions.md)。
- **「依賴注入 / SOLID / Repository？」** → 鬆耦合、可測試、依賴反轉。見 [DI](../16-architecture/03-dependency-injection.md)、[SOLID](../16-architecture/05-solid.md)。

### 資安與系統設計

- **「SQL injection 怎麼防？」** → 參數化查詢（prepared statement）。見 [注入](02-injection.md)。
- **「密碼怎麼存？」** → 慢雜湊 + 加鹽（argon2/bcrypt），別用 SHA-256。見 [密碼雜湊](08-password-hashing.md)。
- **「JWT 原理與陷阱？」** → 三段結構、簽章保完整性非機密、`alg:none`。見 [JWT](04-jwt.md)。
- **「設計短網址 / 限流器 / 分散式 ID？」** → base62、token bucket、Snowflake。見 [短網址](10-system-design-url-shortener.md)、[限流器](11-system-design-rate-limiter.md)、[分散式 ID](13-system-design-distributed-id.md)。
- **「CAP / 一致性 / 冪等？」** → 見 [分散式系統](../22-distributed-systems/README.md)。

## Specification（規範：如何用這份索引複習）

**建議的複習流程**：

1. **自我測驗**：逐條看問題，**先不看連結**，試著在心裡完整回答。
2. **標記卡關**：答得吞吐、講不完整、不確定「為什麼」的，標記起來。
3. **回讀深入**：點進連結章節，重讀 `Interview Notes` 與 `Implementation` 區塊。
4. **口說練習**：把答案講出來（面試是口說，不是默寫）。
5. **重複**：面試前循環幾輪，直到每條都能流暢講清「是什麼 + 為什麼 + 底層」。

**回答的黃金結構**（技術問題通用）：**先給簡潔定義 → 解釋為什麼/底層原理 → 舉例或取捨 → 提及陷阱/最佳實踐**。這正是本書每章的鋪陳方式。

## Code Example（工具：面試複習進度追蹤）

```python
# interview_tracker.py — 面試考點自評進度追蹤（純標準庫，可執行）
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Topic:
    name: str
    confidence: int = 0  # 0=沒把握 1=普通 2=熟練


@dataclass
class ReviewTracker:
    topics: list[Topic] = field(default_factory=list)

    def add(self, name: str, confidence: int) -> None:
        self.topics.append(Topic(name, confidence))

    def weak_spots(self) -> list[str]:
        """列出還沒把握（confidence < 2）的考點，優先複習。"""
        return [t.name for t in self.topics if t.confidence < 2]

    def readiness(self) -> float:
        """整體準備度：熟練考點的比例。"""
        if not self.topics:
            return 0.0
        return sum(t.confidence == 2 for t in self.topics) / len(self.topics)


def main() -> None:
    tracker = ReviewTracker()
    tracker.add("GIL 與並發選型", 2)
    tracker.add("引用計數與 GC", 1)
    tracker.add("SQL injection 防禦", 2)
    tracker.add("JWT 陷阱", 0)
    tracker.add("Snowflake 分散式 ID", 1)

    print(f"整體準備度: {tracker.readiness():.0%}")
    print(f"優先複習（沒把握的）: {tracker.weak_spots()}")


if __name__ == "__main__":
    main()
```

**預期輸出**：

```pycon
$ python interview_tracker.py
整體準備度: 40%
優先複習（沒把握的）: ['引用計數與 GC', 'JWT 陷阱', 'Snowflake 分散式 ID']
```

用這個小工具把上面索引的考點逐一評分，就能算出準備度、列出該優先補的弱項——把「複習」變成可量化、有系統的過程。

## Best Practice（最佳實踐）

- **面試前用這份索引做系統性自我檢測**，別漫無目的地讀。
- **重點放在「為什麼」與底層原理**：面試考深度，不是 API 背誦。
- **口說練習**：能寫不等於能講清楚；面試是口說。
- **每個回答遵循「定義→原理→取捨→陷阱」結構**，完整且有層次。
- **卡關就回讀對應章節的 Interview Notes**，那是濃縮的考點。
- **技術 + 行為兩手準備**（見 [行為面試](14-behavioral-interview.md)）。
- **結合白板題練習**（見 `interview/09-coding-problems.md`）：手寫可跑的程式碼。

## Common Mistakes（常見誤解）

- **只背 API、不懂原理**：面試官一問「為什麼」就露餡。
- **能寫不能講**：默寫得出來，口頭講不清楚——面試吃虧。
- **漫無目的地複習**：不做自我檢測，時間花在已會的、漏掉不熟的。
- **忽略「為什麼這樣設計」**：本書強調的取捨與動機正是面試加分點。
- **只準備技術、輕忽行為面試**：兩者都要（見 [行為面試](14-behavioral-interview.md)）。
- **回答沒有結構**：想到哪講到哪，顯得不清晰；用固定框架。

## Interview Notes（面試重點）

- **把這份索引當面試前的最終檢核表**：逐條能流暢講「是什麼 + 為什麼 + 底層 + 取捨」才算過關。
- **高頻必考**：GIL/並發選型、引用計數與 GC、可變性、MRO、裝飾器、生成器、N+1、SQL injection、密碼雜湊——這些幾乎必問。
- **系統設計**：熟練短網址、限流器、分散式 ID 的核心演算法與取捨。
- **回答結構**：定義 → 原理 → 取捨/舉例 → 陷阱/最佳實踐。
- **深度優先**：面試在意你懂多深，本書的 Implementation 區塊正是為此而寫。

---

⬅️ 這是 Part 20 的最後一章。

[⬆️ 回 Part 20 索引](README.md) ｜ [下一 Part：微服務 ➡️](../21-microservices/README.md)
