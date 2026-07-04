# Part 15 面試題:資料庫

> 對應 [Part 15 資料庫](../chapters/15-database/README.md)。**後端高頻**——SQL injection、ACID/隔離級別、連線池、N+1、索引、Redis 快取。

---

## Q1.(必考)什麼是 SQL injection?怎麼防?

**考點**:DB-API([01-db-api](../chapters/15-database/01-db-api.md))

**答**:SQL injection 是把使用者輸入**拼進 SQL 字串**,讓輸入被當 SQL 執行(如 `"' OR '1'='1"` 繞過登入、`"; DROP TABLE users;"` 刪表)。

**防法:參數化查詢**——值當**純資料**傳給驅動,驅動負責跳脫,值永遠不會被當 SQL:

```python
cursor.execute("SELECT * FROM users WHERE name = ?", (user_input,))   # 安全
cursor.execute(f"SELECT * FROM users WHERE name = '{user_input}'")     # 危險!
```

好處:防注入 + **重用查詢計畫**(效能)。

**追問**:PEP 249 **DB-API 2.0** 是統一介面(換 DB 不用大改);**connection**(管交易、昂貴、長生命週期)vs **cursor**(執行查詢、短暫);不同驅動的 `paramstyle`(`?`/`%s`/`:name`);`executemany` 批次;即使用 ORM 底層仍是 DB-API。

---

## Q2. SQLite 和 PostgreSQL 差在哪?什麼時候該換?

**考點**:sqlite3([02-sqlite3](../chapters/15-database/02-sqlite3.md))

**答**:

| | SQLite | PostgreSQL |
|---|--------|-----------|
| 架構 | **嵌入式**(函式庫 + 檔案) | **client-server**(獨立伺服器) |
| 設定 | 零設定 | 需部署 |
| 併發寫入 | **一次一個寫入者** | 高併發 |
| 適用 | 開發/測試/單機/嵌入 | 生產多使用者 |

**該從 SQLite 換 PostgreSQL 的時機**:多使用者高併發寫入、需要網路存取、需要進階功能。

**追問**:SQLite 陷阱——**外鍵預設關**(要 `PRAGMA foreign_keys = ON`)、動態型別、寫入併發限制;`row_factory = sqlite3.Row`(欄名存取)、`WAL` 模式改善併發、`:memory:` 測試用。

---

## Q3. SQLAlchemy 的 Core 和 ORM 差在哪?ORM 的三大機制?

**考點**:SQLAlchemy([03-sqlalchemy-core](../chapters/15-database/03-sqlalchemy-core.md) / [04-sqlalchemy-orm](../chapters/15-database/04-sqlalchemy-orm.md))

**答**:兩層:

- **Core(SQL Expression Language)**:用 Python 表達式**建構 SQL**、自動參數化、跨方言編譯。適合**重查詢/效能/報表**。
- **ORM**:**物件映射**(建在 Core 上)——把資料列當物件操作,藏 SQL。適合一般 CRUD。

**ORM 三大機制**:

1. **identity map**:同主鍵 = 同一個 Python 物件(`session.get` 不重打 DB)。
2. **unit of work**:追蹤變更,**改物件屬性,session 自動生成 UPDATE**(不用手動 update),`flush` 才送 SQL。
3. **session**:暫存 + 變更追蹤 + 快取。

**追問**:

- **flush vs commit?** → `flush` 送 SQL(尚未提交);`commit` 提交交易。
- **N+1 陷阱?** → lazy loading 造成(見 Q9)。**每請求一個 session**;async 用 `AsyncSession`。

---

## Q4. 連線池為什麼存在?連線洩漏是什麼?

**考點**:連線池([05-connection-pool](../chapters/15-database/05-connection-pool.md))

**答**:建立資料庫連線**昂貴**(TCP + TLS + 認證),**連線池化重用連線省開銷**——正式服務標配。

**連線洩漏(生產頭號事故)**:借了連線**沒還**(忘了 close/歸還)——池被耗盡,新請求全部卡住等連線。防法:**用 `with`/yield 依賴確保歸還**:

```python
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()      # 保證歸還
```

**追問**:關鍵參數 `pool_size`/`max_overflow`(併發上限)、`pool_timeout`(等待)、`pool_recycle` + `pool_pre_ping`(防死連線);**池大小要配合 DB `max_connections` 與應用實例數**(總連線別超上限,別盲目調大);serverless 用 `NullPool`,或用 PgBouncer。

---

## Q5.(必考)什麼是 ACID?四個隔離級別?悲觀鎖和樂觀鎖?

**考點**:交易([06-transactions](../chapters/15-database/06-transactions.md))

**答**:**ACID**:

- **Atomicity(原子性)**:全做或全不做(轉帳:扣款和入帳要嘛都成功要嘛都回滾)。
- **Consistency(一致性)**:交易前後都是合法狀態。
- **Isolation(隔離性)**:並發交易不互相干擾。
- **Durability(持久性)**:提交後即使當機也不丟。

**四個隔離級別**(由鬆到嚴)與對應異常:

| 級別 | 防止 |
|------|------|
| Read Uncommitted | (最鬆,會 dirty read) |
| Read Committed(多數 DB 預設) | 防 dirty read |
| Repeatable Read(MySQL 預設) | 防 non-repeatable read |
| Serializable | 防 phantom read(最嚴) |

**悲觀鎖 vs 樂觀鎖**(並發更新):

- **悲觀鎖(`SELECT ... FOR UPDATE`)**:先鎖住,適合**衝突多**。
- **樂觀鎖(版本號)**:更新時檢查版本沒變才寫,適合**衝突少**。

**追問**:死鎖防範(相同順序取鎖、重試);交易要**短**(持鎖阻塞);用 `with engine.begin()` 管交易邊界。

---

## Q6. 資料庫 migration 是什麼?怎麼做零停機的破壞性變更?

**考點**:migration([07-migration](../chapters/15-database/07-migration.md))

**答**:migration 是「**schema 的版本控制**」——每次變更寫成**有版本、可 upgrade/downgrade 的腳本**,任何環境跑到最新得一致 schema。用 **Alembic**(`alembic_version` 表記錄目前版本、`down_revision` 串版本鏈)。

**零停機的破壞性變更**:**分階段**做——加(新欄)→ 遷移(填資料)→ 切換(程式改用新欄)→ 刪(舊欄)。別一步到位(舊程式會壞)。**大表 ALTER 會鎖表**要小心。

**追問**:`--autogenerate` 比對模型與 DB 差異,但**要 review**(改名、資料遷移偵測不準);migration 進 git;部署含 `alembic upgrade head`;**絕不手動改正式 schema**。

---

## Q7. Redis 為什麼快?cache-aside 模式?快取三大問題?

**考點**:Redis([08-redis](../chapters/15-database/08-redis.md))

**答**:Redis 是**記憶體儲存**,讀取比 DB 快百倍,降 DB 負載。

**cache-aside 模式**:讀時**先查快取,miss 才查 DB 並寫回**;寫時**刪快取**(下次讀重建)。

**快取三大問題**:

| 問題 | 成因 | 解法 |
|------|------|------|
| **穿透** | 查不存在的 key 一直打 DB | 快取 null / 布隆過濾器 |
| **雪崩** | 大量 key 同時過期 | TTL 加隨機抖動 |
| **擊穿** | 熱點 key 過期瞬間大量請求 | 鎖 / 熱點不過期 |

**追問**:快取一致性難(資料變了快取怎辦——寫時失效 + TTL 安全網,本質**最終一致**);Redis **不只快取**:session store、限流、任務佇列、排行榜(sorted set)、分散式鎖、pub/sub;序列化用 JSON 別 pickle。

---

## Q8. 為什麼 async 端點需要 async 資料庫驅動?

**考點**:async DB([09-async-database](../chapters/15-database/09-async-database.md))

**答**:**同步 DB 查詢會阻塞 event loop**——所有並發請求停擺(同 [Part 09/14 的阻塞陷阱](part14-web.md#q9必考在-async-def-端點裡放阻塞操作會怎樣))。async 驅動(asyncpg)讓 DB I/O **非阻塞、可並發**。

**一路 async**:async 端點用 async 驅動 + `AsyncSession`、全程 await;否則用 `def` 端點(執行緒池)。

**追問**:

- **async 兩大陷阱?** → 不能隱式 lazy loading(要 eager,見 Q9);session **不能跨 task 共用**(非並發安全)。
- **async 永遠更快?** → **不是**。高並發 I/O bound 才值得;CPU bound/低並發/批次用同步。

---

## Q9.(必考)N+1 問題是什麼?怎麼解?

**考點**:N+1([10-n-plus-1](../chapters/15-database/10-n-plus-1.md))

**答**:**lazy loading + 迴圈存取關聯** → 1 次查主體 + N 次查各關聯 = **1+N 次查詢**,資料多時效能災難:

```python
authors = session.query(Author).all()   # 1 次
for a in authors:
    print(a.books)                        # 每個作者各查一次 → N 次!
```

**解法:eager loading**(一次查完關聯):

- **`selectinload`**:額外一次 `IN` 查詢,適合**一對多/多對多**。
- **`joinedload`**:用 JOIN,適合**多對一/一對一**(一對多用它會列爆炸)。

**追問**:lazy 也有適用場景(不一定用到的關聯);**async 必須顯式 eager**(不能隱式 lazy);用 `echo=True` 偵測 N+1、把每請求查詢數納入觀測——**ORM 不會自動幫你優化**。

---

## Q10.(必考)索引怎麼運作?該對哪些欄位加?什麼情況索引會失效?

**考點**:索引([11-indexing](../chapters/15-database/11-indexing.md))

**答**:索引(B-tree)讓查找從**全表掃描 O(n) 變 O(log n)**、支援範圍查詢;代價是**佔空間 + 拖慢寫入**(用寫換讀)。

**該加索引的欄位**:WHERE/JOIN/ORDER BY 的**高選擇性**欄位(值分散,如 email)。**低選擇性欄位(如性別、布林)加索引沒用**(值太少,索引幫不上)。

**複合索引的最左前綴原則**:`INDEX(a, b, c)` 能用於 `WHERE a`、`WHERE a AND b`,但**跳過最左欄(只查 b)用不到**。

**索引失效的情況**:

- 索引欄**包函式/運算**(`WHERE UPPER(name) = ...`)。
- **前置 `%` 的 LIKE**(`LIKE '%abc'`)。
- **型別不符**(字串欄用數字查)。
- 跳過最左欄。

**追問**:用 **`EXPLAIN`/`EXPLAIN ANALYZE`** 驗證查詢計畫(Index Scan vs Seq Scan),**先量測再優化**;進階:覆蓋索引、keyset(cursor)分頁。

---

⬅️ [Part 14](part14-web.md) ｜ [索引](README.md) ｜ ➡️ [Part 16 架構與設計](part16-architecture.md)
