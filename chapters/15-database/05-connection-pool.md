# 連線池

> 建立資料庫連線很昂貴（TCP 握手、認證），每次查詢都新建會拖垮效能。連線池預先建好一批連線、重複使用——這是所有正式服務的標配。搞懂它的參數，才能調出對的併發能力。

## Why（為什麼）

建立一條資料庫連線成本很高：TCP 三次握手、TLS 協商、資料庫認證、配置伺服器端資源——可能耗時數十毫秒。若每次查詢都 `connect()` 再 `close()`，在高流量下這開銷會壓垮應用（連線建立的時間可能比查詢本身還久）。**連線池（connection pool）** 解法：**預先建立一批連線放在池子裡，需要時借出、用完歸還（而非關閉）**，重複使用。這是所有正式資料庫應用的標配。但連線池不是設了就好——**池大小、逾時、回收**等參數設錯會導致「連線耗盡」「用到失效連線」等問題。理解連線池讓你的服務在高併發下穩定。

## Theory（理論：借還模型與池大小）

連線池的模型很像「共享單車」：

- 池中預先放 N 條已建立的連線。
- 程式要查詢時**借一條**（checkout）；池中有空閒就給，沒有就等（或再開新的，到上限）。
- 用完**歸還**（checkin）——連線不關閉，回池中待下次用。

關鍵參數是**池大小**。它決定「同時能有多少查詢在進行」：

- **太小**：高併發時連線不夠，請求排隊等連線（延遲飆高、甚至逾時）。
- **太大**：佔用過多資料庫端資源（每條連線在 DB 端也耗記憶體），資料庫本身有連線數上限（PostgreSQL 預設 `max_connections=100`），超過就拒絕。

**池大小要配合資料庫的連線上限與應用的併發模型**。一個常見公式思路：總連線數（所有應用實例 × 每實例池大小）不能超過資料庫 `max_connections`（還要留給其他客戶端）。

## Specification（規範：SQLAlchemy 連線池參數）

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg://user:pass@localhost/db",
    pool_size=5,          # 池中常駐連線數
    max_overflow=10,      # 尖峰時可額外開的連線數（pool_size + max_overflow = 硬上限）
    pool_timeout=30,      # 借連線等不到時，最多等幾秒（超過拋錯）
    pool_recycle=1800,    # 連線用超過 N 秒就回收重建（防 DB/防火牆斷掉失效連線）
    pool_pre_ping=True,   # 借出前先 ping 測試連線是否還活著（防用到死連線）
)
# Engine 內建連線池；一個 engine 全應用共用（別重複建）
```

| 參數 | 作用 | 設錯的後果 |
|------|------|-----------|
| `pool_size` | 常駐連線數 | 太小→排隊；太大→耗 DB 資源 |
| `max_overflow` | 尖峰額外連線 | 硬上限 = pool_size + overflow |
| `pool_timeout` | 借不到連線的等待上限 | 太短→尖峰易失敗；太長→請求卡住 |
| `pool_recycle` | 連線最大存活秒數 | 防用到被 DB/防火牆斷掉的死連線 |
| `pool_pre_ping` | 借出前健康檢查 | 避免「MySQL server has gone away」 |

## Implementation（借還、耗盡、失效連線、併發配置）

### 一個 Engine 共用（別重複建）

**Engine 內建連線池，全應用共用一個 engine**（模組層級建立一次）——每個 engine 有獨立的池，重複建 engine = 重複建池 = 浪費：

```python
# db.py — 全應用共用
from sqlalchemy import create_engine

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)

# 其他模組 import 這個 engine，別各自 create_engine
```

### 連線耗盡：最常見的生產事故

若連線借出後**沒歸還**（忘了關 session/connection），池會被榨乾——後續請求借不到連線、卡在 `pool_timeout` 後拋 `TimeoutError`。**務必確保連線用完歸還**（用 `with` 或 yield 依賴）：

```python
# ✅ 用 with 確保歸還（即使出錯）
with engine.connect() as conn:
    conn.execute(...)
# 區塊結束 → 連線自動歸還池中（不是關閉）

# ✅ FastAPI：yield 依賴確保每請求 session 歸還
def get_session():
    with Session(engine) as session:
        yield session          # 請求結束自動關閉 → 歸還池

# 🔴 洩漏：借了不還 → 池耗盡
conn = engine.connect()
conn.execute(...)
# 忘了 conn.close() → 這條連線永遠不回池
```

**連線洩漏**是資料庫相關生產事故的頭號原因之一：症狀是「一開始正常，跑一陣子後所有請求都逾時」。用 `with`/依賴注入根治。

### 失效連線：pool_recycle 與 pre_ping

池中的連線可能「悄悄死掉」——資料庫重啟、防火牆/雲負載平衡器閒置逾時切斷、DB 端 `wait_timeout` 到期。若借到這種死連線，查詢會報錯（如 MySQL 的「server has gone away」）。兩道防線：

- **`pool_recycle`**：連線存活超過 N 秒就丟棄重建（設得比 DB/防火牆的 idle timeout 短）。
- **`pool_pre_ping=True`**：每次借出前先發一個輕量測試查詢，確認連線還活著；死了就換一條。

生產環境**強烈建議開 `pool_pre_ping`**——用一點點開銷換「不會用到死連線」的穩定性。

### 連線池大小怎麼設

考量點：

1. **資料庫的 `max_connections`**：所有客戶端連線總和不能超過。
2. **應用實例數**：水平擴展（見 [Kubernetes](../19-cloud-native/06-kubernetes.md)）時，總連線 = 實例數 × (pool_size + max_overflow)。
3. **併發模型**：同步 worker（每 worker 一次一個查詢）vs async（一個 worker 可多併發查詢）需求不同。

```text
例：PostgreSQL max_connections=100，跑 10 個應用實例
   每實例 pool_size + max_overflow 應 ≲ 8（10×8=80，留 20 給其他）
```

**別盲目調大池**——資料庫連線是稀缺資源。連線太多反而讓資料庫變慢（context switch、記憶體）。若真的需要大量連線，考慮外部連線池器如 **PgBouncer**（在資料庫前面再做一層池化）。

### 不同的池策略

SQLAlchemy 有多種池類別，依場景選：

- **`QueuePool`（預設）**：標準借還池，適合大多數服務。
- **`NullPool`**：不池化（每次新建、用完關）。適合 serverless（見 [Serverless](../19-cloud-native/08-serverless.md)）或每個連線該獨立的場景。
- **`StaticPool`**：單一連線，常用於 SQLite `:memory:` 測試（讓多處共用同一記憶體 DB）。

## Code Example（可執行的 Python 範例）

```python
# connection_pool_demo.py — 模擬連線池借還與耗盡（可獨立測試）
from __future__ import annotations


class ConnectionPool:
    """模擬連線池的借還與上限。"""

    def __init__(self, pool_size: int, max_overflow: int) -> None:
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.hard_limit = pool_size + max_overflow
        self.checked_out = 0  # 目前借出的連線數
        self.created = 0  # 曾建立的連線總數（觀察重用）

    def acquire(self) -> str:
        """借一條連線。"""
        if self.checked_out >= self.hard_limit:
            raise TimeoutError(f"連線池耗盡（上限 {self.hard_limit}），請求需等待")
        self.checked_out += 1
        # 池內有空閒就重用，否則新建
        if self.checked_out > self.created:
            self.created += 1
        return f"連線#{self.checked_out}"

    def release(self) -> None:
        """歸還連線（不關閉，回池中）。"""
        if self.checked_out > 0:
            self.checked_out -= 1


def demo() -> None:
    pool = ConnectionPool(pool_size=2, max_overflow=1)  # 硬上限 3
    print(f"池設定: pool_size=2, max_overflow=1, 硬上限={pool.hard_limit}")

    # 借還重用：連線被重複使用（created 不隨每次借而增加）
    print("\n正常借還（連線重用）：")
    for i in range(4):
        conn = pool.acquire()
        print(f"  借出 {conn}（曾建立 {pool.created} 條）")
        pool.release()  # 用完歸還
    print(f"  → 4 次查詢只建立了 {pool.created} 條連線（重用！）")

    # 連線耗盡：借了不還
    print("\n連線洩漏（借了不還）：")
    held = [pool.acquire() for _ in range(3)]  # 借滿 3 條不還
    print(f"  借出 {len(held)} 條未歸還")
    try:
        pool.acquire()  # 第 4 條 → 耗盡
    except TimeoutError as e:
        print(f"  第 4 次借連線: {e}")

    print("\n重點：連線池重用連線省開銷；借了要還，否則耗盡（生產頭號事故）")


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python connection_pool_demo.py
池設定: pool_size=2, max_overflow=1, 硬上限=3

正常借還（連線重用）：
  借出 連線#1（曾建立 1 條）
  借出 連線#1（曾建立 1 條）
  借出 連線#1（曾建立 1 條）
  借出 連線#1（曾建立 1 條）
  → 4 次查詢只建立了 1 條連線（重用！）

連線洩漏（借了不還）：
  借出 3 條未歸還
  第 4 次借連線: 連線池耗盡（上限 3），請求需等待

重點：連線池重用連線省開銷；借了要還，否則耗盡（生產頭號事故）
```

## Diagram（圖解：連線池借還）

```mermaid
flowchart TD
    A["應用請求查詢"] --> B{池中有空閒連線?}
    B -->|有| C["借出(checkout)"]
    B -->|"無 且 未達上限"| D["新建連線"]
    B -->|"無 且 已達上限"| E["等待 pool_timeout<br/>逾時→TimeoutError"]
    C --> F["執行查詢"]
    D --> F
    F --> G["歸還(checkin)<br/>連線回池, 不關閉"]
    G --> B
    style C fill:#e8f5e9
    style E fill:#ffebee
    style G fill:#e3f2fd
```

## Best Practice（最佳實踐）

- **全應用共用一個 Engine**（內建池），別重複 `create_engine`。
- **務必歸還連線**（`with` / yield 依賴）：連線洩漏會耗盡池——生產頭號事故。
- **生產開 `pool_pre_ping=True`**：避免用到被斷掉的死連線。
- **設 `pool_recycle` 短於 DB/防火牆的 idle timeout**：主動回收防失效。
- **池大小配合 DB `max_connections` 與實例數**：總連線別超過 DB 上限；別盲目調大。
- **大量連線需求用 PgBouncer** 等外部池化器（見 [Serverless](../19-cloud-native/08-serverless.md)）。
- **serverless 用 `NullPool` 或外部池**：函式短命、連線不宜長持。
- **監控連線池指標**（借出數、等待時間）：及早發現洩漏或池太小。

## Common Mistakes（常見誤解）

- **連線洩漏（借了不還）**：忘了 `close()`/沒用 `with`——池耗盡、請求逾時；用 `with`/依賴注入根治。
- **每次查詢 `create_engine`/`connect` 新連線**：失去池化意義、開銷巨大。
- **池設太大**：超過 DB `max_connections`、耗 DB 資源、反而變慢。
- **不開 `pool_pre_ping`/`pool_recycle`**：用到死連線報「server has gone away」。
- **多實例沒算總連線數**：10 實例 × 大池 = 撐爆 DB 連線上限。
- **async 應用用同步池/Session**：阻塞 event loop（見 [async DB](09-async-database.md)）。
- **以為連線池能無限擴充併發**：DB 連線是稀缺資源，超過反效果。

## Interview Notes（面試重點）

- **能說出連線池為何存在：建立連線昂貴（TCP/TLS/認證），池化重用連線省開銷**——正式服務標配。
- **知道連線洩漏（借了不還）會耗盡池、是生產頭號事故**，用 `with`/yield 依賴確保歸還。
- 知道關鍵參數：`pool_size`/`max_overflow`（併發上限）、`pool_timeout`（等待）、`pool_recycle` + `pool_pre_ping`（防死連線）。
- **知道池大小要配合 DB `max_connections` 與應用實例數**（總連線別超上限），別盲目調大。
- 知道 `NullPool`（serverless）、外部池化器 PgBouncer、async 要用 async 引擎/池。

---

➡️ 下一章：[transaction 交易](06-transactions.md)

[⬆️ 回 Part 15 索引](README.md)
