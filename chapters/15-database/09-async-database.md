# async 資料庫存取

> async Web（FastAPI）要一路 async 到底——但同步的 DB 查詢會卡住整個 event loop。async 資料庫驅動（asyncpg、SQLAlchemy async）讓資料庫 I/O 也非阻塞，一個 worker 就能並發處理大量查詢。這章講 async DB 的用法與陷阱。

## Why（為什麼）

FastAPI 的高並發來自 async（見 [async Web](../14-web/12-async-web-background.md)、[asyncio](../09-concurrency/07-asyncio-basics.md)）——一個 worker 在等 I/O 時處理別的請求。但**資料庫查詢也是 I/O**（等網路、等 DB 運算）。如果你在 `async def` 端點裡用**同步**的 DB 驅動（`psycopg2`、同步 SQLAlchemy），查詢會**阻塞整個 event loop**——所有並發請求停擺，async 的好處全毀。**async 資料庫驅動**（`asyncpg`、`aiomysql`、SQLAlchemy 的 `AsyncSession`）讓資料庫 I/O 也 `await`（非阻塞），等查詢時 event loop 能處理別的請求。這是「一路 async 到底」的最後一塊拼圖。理解何時該用 async DB、它的陷阱（session 不能共用等），是寫高並發 FastAPI 服務的關鍵。

## Theory（理論：非阻塞 DB I/O）

同步 DB 查詢的問題：`cursor.execute(...)` 會**阻塞**——執行緒卡在那裡等 DB 回應（可能數十毫秒）。在同步 Web（每請求一執行緒）沒問題（那個執行緒本來就專屬該請求）。但在 **async Web（單執行緒 event loop）**，一個阻塞查詢卡住 event loop，期間所有其他請求都不能進展。

async DB 驅動用**非阻塞 I/O**：`await conn.execute(...)` 時，若在等 DB，控制權**交還 event loop** 去處理別的請求；DB 回應後再回來。這樣一個 worker 能同時「進行中」大量查詢（都在等 DB）。

**關鍵原則**（同 [async Web](../14-web/12-async-web-background.md)）：**async 端點要一路 async——用 async DB 驅動；否則就用同步端點（`def`，FastAPI 丟執行緒池）**。最糟的是「async 端點裡用同步 DB」。

## Specification（規範：SQLAlchemy async）

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

# 1. async 引擎（用 async 驅動：asyncpg / aiosqlite）
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
# SQLite async: "sqlite+aiosqlite:///app.db"

# 2. async session 工廠
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# 3. async 查詢（全部 await）
async def get_user(user_id: int):
    async with AsyncSessionLocal() as session:       # async context manager
        result = await session.execute(              # await 查詢
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

# 4. FastAPI 依賴（每請求一個 async session）
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/users/{id}")
async def read_user(id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == id))
    return result.scalar_one_or_none()
```

## Implementation（async 驅動、AsyncSession、陷阱、何時用）

### async 驅動與引擎

async 需要 **async 版的驅動**（同步驅動不行）：

| 資料庫 | 同步驅動 | async 驅動 |
|--------|---------|-----------|
| PostgreSQL | psycopg2 / psycopg | **asyncpg** / psycopg(async) |
| MySQL | mysqlclient | **aiomysql** / asyncmy |
| SQLite | sqlite3 | **aiosqlite** |

連線字串指定 async 驅動：`postgresql+asyncpg://...`、`sqlite+aiosqlite:///...`。用 `create_async_engine` 建引擎。

### AsyncSession：全程 await

async ORM 用 `AsyncSession`，所有 DB 操作都要 `await`：

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def create_order(session: AsyncSession, user_id: int, amount: int) -> Order:
    order = Order(user_id=user_id, amount=amount)
    session.add(order)                    # add 不需 await（只是加入追蹤）
    await session.commit()                # commit 要 await（實際 I/O）
    await session.refresh(order)          # refresh 要 await
    return order

async def list_orders(session: AsyncSession, user_id: int) -> list[Order]:
    result = await session.execute(       # execute 要 await
        select(Order).where(Order.user_id == user_id)
    )
    return list(result.scalars().all())
```

**規則**：任何觸發 DB I/O 的操作（`execute`/`commit`/`refresh`/`get`/`flush`）都要 `await`；純記憶體操作（`add`）不用。

### 🔴 陷阱一：lazy loading 在 async 不能隱式觸發

async 下，關聯的 **lazy loading（見 [N+1](10-n-plus-1.md)）不能隱式運作**——因為 lazy load 需要在存取屬性時「偷偷發 DB 查詢」，但 async 的 I/O 必須顯式 `await`，屬性存取沒法 await。存取未載入的關聯會拋錯（`MissingGreenlet`）。**解**：用 **eager loading** 預先載入（`selectinload`/`joinedload`）：

```python
from sqlalchemy.orm import selectinload

# ✅ 用 eager loading 預載關聯（async 必須）
result = await session.execute(
    select(User).where(User.id == 1).options(selectinload(User.orders))
)
user = result.scalar_one()
for order in user.orders:      # 已預載，不需再查（也不會出錯）
    print(order.amount)

# 🔴 async 下沒預載就存取 user.orders → MissingGreenlet 錯誤
```

### 🔴 陷阱二：session/連線不能跨 task 共用

`AsyncSession` **不是並發安全的**——別把同一個 session 給多個並發 task（`asyncio.gather`）同時用，會出錯或資料錯亂。每個並發工作單元用**各自的 session**：

```python
# 🔴 錯：多 task 共用一個 session
async def bad(session):
    await asyncio.gather(q1(session), q2(session))   # 共用 session，危險

# ✅ 對：各自的 session
async def good():
    async def task():
        async with AsyncSessionLocal() as session:
            return await session.execute(...)
    await asyncio.gather(task(), task())             # 各自 session
```

### 何時用 async DB（別無腦用）

async DB **不是永遠更快**——它增加複雜度，只在對的場景有價值：

- **值得用**：高並發 I/O bound 服務（大量請求、每個都查 DB/呼叫外部）、已經是 async 應用（FastAPI async 端點）。
- **不值得**：CPU bound、低並發、簡單腳本、批次 ETL——同步更簡單，async 沒好處。
- **混用**：同步 DB 在 async 應用可行——用 `def` 端點（FastAPI 丟執行緒池，見 [async Web](../14-web/12-async-web-background.md)），或 `asyncio.to_thread`（見 [to_thread](../09-concurrency/11-blocking-in-async.md)）。

**別在 `async def` 裡用同步 DB 驅動**（阻塞 event loop）——要嘛全 async DB、要嘛用 `def` 端點。

### 連線池

async 引擎也有連線池（見 [連線池](05-connection-pool.md)）——概念相同（借還、大小、pre_ping），但用 async 版。注意 async 池大小要配合 event loop 的並發量。

## Code Example（可執行的 Python 範例）

```python
# async_db_demo.py — 用 aiosqlite 概念模擬 async DB 並發（可獨立執行）
from __future__ import annotations

import asyncio
import time


class AsyncFakeDB:
    """模擬 async 資料庫：查詢是非阻塞 I/O（await）。"""

    def __init__(self) -> None:
        self.users = {1: "Alice", 2: "Bob", 3: "Cara"}

    async def get_user(self, user_id: int) -> str | None:
        await asyncio.sleep(0.1)  # 模擬非阻塞 DB I/O（等網路/DB）
        return self.users.get(user_id)


async def sequential(db: AsyncFakeDB, ids: list[int]) -> tuple[list[str | None], float]:
    """逐一查詢（每個 await 完才下一個）。"""
    start = time.monotonic()
    results = [await db.get_user(i) for i in ids]
    return results, time.monotonic() - start


async def concurrent(db: AsyncFakeDB, ids: list[int]) -> tuple[list[str | None], float]:
    """並發查詢（gather，多查詢同時等 I/O）。"""
    start = time.monotonic()
    results = await asyncio.gather(*(db.get_user(i) for i in ids))
    return list(results), time.monotonic() - start


async def main() -> None:
    db = AsyncFakeDB()
    ids = [1, 2, 3]

    seq_results, seq_time = await sequential(db, ids)
    print(f"逐一查詢: {seq_results}，耗時 {seq_time:.2f}s（3 × 0.1s）")

    con_results, con_time = await concurrent(db, ids)
    print(f"並發查詢: {con_results}，耗時 {con_time:.2f}s（同時等 I/O）")

    print(f"\n並發快了約 {seq_time / con_time:.1f} 倍（async DB 讓查詢並發）")
    print("重點：async DB 讓 I/O 非阻塞、可並發；要一路 await、用 async 驅動")


if __name__ == "__main__":
    asyncio.run(main())
```

**預期輸出**：

```pycon
$ python async_db_demo.py
逐一查詢: ['Alice', 'Bob', 'Cara']，耗時 0.30s（3 × 0.1s）
並發查詢: ['Alice', 'Bob', 'Cara']，耗時 0.10s（同時等 I/O）

並發快了約 3.0 倍（async DB 讓查詢並發）
重點：async DB 讓 I/O 非阻塞、可並發；要一路 await、用 async 驅動
```

## Diagram（圖解：同步 vs async DB 在 event loop）

```mermaid
flowchart TD
    subgraph sync [async 端點裡用同步 DB 🔴]
        A["請求A: 同步查詢(阻塞)"] --> B["event loop 卡住<br/>請求B/C 停擺"]
    end
    subgraph async [async 端點 + async DB ✅]
        C["請求A: await 查詢"] --> D["等 DB 時交還 loop"]
        D --> E["處理請求B/C(並發)"]
    end
    style B fill:#ffebee
    style E fill:#e8f5e9
```

## Best Practice（最佳實踐）

- **async 端點用 async DB 驅動**（asyncpg/aiomysql/aiosqlite + `AsyncSession`）：一路 async、非阻塞。
- **所有 DB I/O 都 `await`**（execute/commit/refresh/get）；純記憶體操作（add）不用。
- **async 一定用 eager loading**（`selectinload`/`joinedload`）：async 不能隱式 lazy load（見 [N+1](10-n-plus-1.md)）。
- **每工作單元/請求一個 session，別跨 task 共用**（AsyncSession 非並發安全）。
- **並發查詢各自 session + `asyncio.gather`**：真正並發。
- **別在 `async def` 用同步 DB**（阻塞 loop）；同步 DB 就用 `def` 端點或 `to_thread`。
- **async 不是永遠更快**：高並發 I/O bound 才值得；CPU bound/低並發/批次用同步。
- **async 連線池配合並發量**（見 [連線池](05-connection-pool.md)）。

## Common Mistakes（常見誤解）

- **在 `async def` 裡用同步 DB 驅動**（psycopg2/同步 Session）：阻塞整個 event loop——async DB 頭號錯誤。
- **async 下隱式 lazy loading**：存取未預載關聯拋 `MissingGreenlet`；用 eager loading。
- **多並發 task 共用一個 AsyncSession**：非並發安全、資料錯亂；各自 session。
- **忘了 await DB 操作**：拿到 coroutine 而非結果、或警告未 await。
- **無腦全上 async**：CPU bound/簡單腳本用 async 只增複雜度沒好處。
- **用同步驅動配 async 引擎**：`create_async_engine` 需要 async 驅動（asyncpg 等）。
- **async session 也用 `expire_on_commit=True`**：commit 後存取屬性觸發 I/O 在 async 麻煩；常設 `expire_on_commit=False`。

## Interview Notes（面試重點）

- **能說出為何 async 端點需要 async DB**：同步 DB 查詢阻塞 event loop、所有並發請求停擺；async 驅動讓 DB I/O 非阻塞可並發。
- **知道「一路 async」**：async 端點用 async 驅動（asyncpg 等）+ `AsyncSession`、全程 await；否則用 `def` 端點（執行緒池）。
- **知道 async 的兩大陷阱**：不能隱式 lazy loading（要 eager loading）、session 不能跨 task 共用（非並發安全）。
- **知道 async 不是永遠更快**：高並發 I/O bound 才值得，CPU bound/低並發/批次用同步。
- 能連結 [async Web](../14-web/12-async-web-background.md)、[N+1](10-n-plus-1.md)、[連線池](05-connection-pool.md)。

---

➡️ 下一章：[N+1 問題與 eager / lazy loading](10-n-plus-1.md)

[⬆️ 回 Part 15 索引](README.md)
