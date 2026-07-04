# Part 15 面試題:資料庫

> 對應 [Part 15 資料庫](../chapters/15-database/README.md)。分兩部分:**原理篇(T1–T10)**——關聯模型、SQL 語意、索引 B+tree、優化器、交易 MVCC、WAL、複製分片、NoSQL 選型;**操作篇(Q1–)**——SQL injection、ACID/隔離級別、連線池、N+1、索引、Redis。後端與資料工程高頻。

---

# 原理篇(資料庫引擎)

## T1. 關聯代數與 SQL 的關係?join 的本質是什麼?

**考點**:關聯式模型([01-relational-model](../chapters/15-database/01-relational-model.md))

**答**:關聯是**元組的集合**(無序、去重、每格單值);**關聯代數**(σ 選擇/π 投影/⋈ join/∪∩−)是作用在關聯上、結果仍是關聯的封閉運算,是 **SQL 的數學骨架**。SQL 宣告式查詢被轉成關聯代數樹,優化器靠等價律重寫它。

**join 的本質 = 笛卡兒積 + 選擇**(配對 + 過濾)——所以沒有 join 條件會產生 N×M 的笛卡兒積爆炸;真實 DB 用 hash/index 避免真的做積,但語意等價。

**追問**:鍵的層次(superkey⊇candidate⊇primary);外鍵=參照完整性;宣告式 + 資料獨立性為何是革命(查詢與存取路徑解耦);集合 vs SQL 的 bag(多重集)語意(SQL 保留重複)。

---

## T2.(必考)NULL 的三值邏輯?為什麼 `NOT IN` 遇到 NULL 會出錯?

**考點**:SQL 語言([02-sql-language](../chapters/15-database/02-sql-language.md))

**答**:NULL 意思是「**未知**」,任何與它的比較結果是 **UNKNOWN**,而 `WHERE` 只保留 **TRUE**。所以 `WHERE x = NULL` 永遠查不到(要用 `IS NULL`);`NULL = NULL` 也是 UNKNOWN。

**`NOT IN (含 NULL 子查詢)` 回空集合**:`x NOT IN (1,2,NULL)` = `x<>1 AND x<>2 AND x<>NULL`,最後一項恆 UNKNOWN,`任何 AND UNKNOWN` 不可能 TRUE → 全被過濾。解法:`NOT EXISTS`(對 NULL 安全)或濾掉 NULL。

**追問**:邏輯處理順序(FROM→WHERE→GROUP BY→HAVING→SELECT→ORDER BY),解釋為何 WHERE 不能用 SELECT 別名、過濾聚合要用 HAVING;`LEFT JOIN` 被 `WHERE` 過濾右表降級成 INNER(條件放 ON)。

---

## T3. 正規化解決什麼?2NF/3NF 差在哪?何時反正規化?

**考點**:正規化([03-normalization](../chapters/15-database/03-normalization.md))

**答**:正規化用**函數相依**消除**冗餘**與三種異常(更新/插入/刪除異常),根源都是「同一事實存多份」。口訣:非鍵欄位相依於 **the key, the whole key, and nothing but the key**——2NF 消**部分相依**(複合鍵下欄位只依賴部分鍵)、3NF 消**遞移相依**(非鍵依賴另一非鍵)。

**反正規化**:讀多/JOIN 是瓶頸、OLAP 星狀模型、NoSQL 內嵌時,刻意冗餘換讀取速度,代價是要維護一致性。**先正規化,有明確理由再反正規化**。

**追問**:BCNF;拆表後外鍵保參照完整性;OLTP 正規化 vs OLAP 反正規化。

---

## T4. B-tree 與 LSM-tree 差在哪?行式與欄式?

**考點**:儲存引擎([04-storage-engine](../chapters/15-database/04-storage-engine.md))

**答**:資料以**固定大小的頁**存放、經 **buffer pool** 在記憶體/磁碟間搬運;**磁碟 I/O 是頭號成本**,設計都在減少它、把隨機 I/O 變順序。

- **B-tree**:就地更新、讀快,傳統關聯式(PostgreSQL/MySQL)。**LSM-tree**:只追加(memtable→SSTable)、寫快、後台 compaction,寫入密集場景(Cassandra/RocksDB)。
- **行式**:一列欄位相鄰,OLTP 讀整列快。**欄式**:一欄值相鄰,OLAP 掃描聚合快、壓縮率高(只讀需要的欄)。

**追問**:為何「讀 1 列 = 讀整頁」;buffer pool 命中率;聚簇 vs 堆積表。

---

## T5.(必考)為什麼索引是 B+tree?複合索引的最左前綴?

**考點**:索引內部([05-index-internals](../chapters/15-database/05-index-internals.md))

**答**:B+tree 是**高扇出、平衡、葉子有序 + 鏈結**的磁碟優化樹——高扇出→樹矮(百萬筆只 3~4 層)→查一筆只幾次 I/O(O(log n) 大底數);葉子有序 + 雙向鏈結→支援**範圍查詢與排序**。對比:二元樹太高、雜湊不支援範圍。

**最左前綴**:`INDEX(a,b,c)` 依字典序排,能加速 `a=?`、`a=? AND b=?`,但 **`WHERE b=?` 用不到**(缺最左 a);範圍條件會終止後續欄使用。

**追問**:覆蓋索引(索引含查詢所需全部欄,**免回表**);聚簇 vs 次要索引;為什麼「有索引卻沒用到」(對欄運算/函式、`LIKE '%x'`、低選擇性)。

---

## T6. 三種 JOIN 演算法?為什麼優化器有時選全表掃描而非索引?

**考點**:查詢優化器([06-query-processing](../chapters/15-database/06-query-processing.md))

**答**:優化器把 SQL 轉代數樹,做**邏輯重寫**(選擇下推等)+ **成本式物理選擇**(靠統計估選擇性)。三種 JOIN:**nested loop**(小表 + 內表有索引)、**hash join**(大表等值、無索引)、**merge join**(兩表已排序)。

**為何選全表掃描**:當查詢要讀的列**佔比高(低選擇性)**,用索引要對大量列「定位 + 隨機回表」,比**順序全表掃描**還貴——所以優化器(正確地)選 Seq Scan。索引適合撈一小撮(高選擇性)。

**追問**:統計過期會選爛計畫(要 `ANALYZE`);讀 `EXPLAIN` 看掃描方式/JOIN/估計 vs 實際列數。

---

## T7.(必考)隔離級別與並發異常?鎖 vs MVCC?

**考點**:交易並發([07-transactions-concurrency](../chapters/15-database/07-transactions-concurrency.md))

**答**:三種讀異常——**髒讀**(讀到未 commit)、**不可重複讀**(同列讀兩次值不同)、**幻讀**(同條件查兩次列數不同)。四個隔離級別用「允許哪些異常」界定:Read Uncommitted→Read Committed(多數預設,防髒讀)→Repeatable Read→Serializable(全防)。

**鎖(悲觀)**:讀寫前加鎖、讀擋寫、2PL 保序、易死鎖。**MVCC(樂觀讀)**:每寫產生新版本、交易讀一致快照、**讀不擋寫**(讀舊版本不必等),代價是要清理舊版本(PostgreSQL 的 VACUUM)。主流 DB 用 MVCC。

**追問**:死鎖=等待成環,偵測(等待圖找環)+ rollback 犧牲者,預防用固定加鎖順序;丟失更新用 `SELECT FOR UPDATE` 或樂觀鎖;write skew 要 Serializable。

---

## T8. WAL 是什麼?為什麼它同時保證原子性與持久性?

**考點**:WAL 與恢復([08-wal-recovery](../chapters/15-database/08-wal-recovery.md))

**答**:**WAL(Write-Ahead Log)** 的黃金規則:**改資料頁之前,先把改動順序寫進 log 並落盤**。於是 **commit = WAL 落盤**(不必等資料頁刷回)——既快(順序寫)又持久。

崩潰後恢復:**redo** 已 commit 但沒刷盤的改動(保**持久性 D**)、**undo** 未 commit 的改動(保**原子性 A**)。checkpoint 定期刷 dirty page + 標記,限制恢復要重做的 WAL 範圍。

**追問**:為何 WAL 又快又安全(順序寫取代多次隨機資料頁寫);group commit 攤平 fsync;關 fsync 快但斷電丟 commit;WAL 也是複製與 PITR 的基礎。

---

## T9. 複製、分割、分片差在哪?什麼是複製延遲?

**考點**:複製與分片([09-replication-sharding](../chapters/15-database/09-replication-sharding.md))

**答**:**複製**=同一份資料多份完整副本(讀取擴展 + 高可用);**分割**=切大表;**分片**=水平切開分散到多台(資料量/寫入擴展)。

**複製延遲(replication lag)**:非同步複製下複本落後主庫 → 寫後立刻讀複本會**讀到舊值**(讀己之寫問題);解法讀主庫或會話一致性。**先垂直擴展、加快取/索引,真的需要才水平分片**(跨分片查詢/交易極難)。

**追問**:同步 vs 非同步複製(強一致慢 vs 快但延遲);分片策略(範圍熱點 vs 雜湊難範圍、取模擴容要大搬移→用一致性雜湊);failover 可能丟未複製 commit(CAP 在 DB 層);**複製 ≠ 備份**。

---

## T10. NoSQL 各家族?怎麼選資料庫?

**考點**:NoSQL 選型([10-nosql-selection](../chapters/15-database/10-nosql-selection.md))

**答**:NoSQL 為擴展/彈性/特定存取模式,**放棄**關聯式的強一致/join/彈性查詢(**不是「更好」**)。四大家族:文件(MongoDB)、KV(Redis/DynamoDB)、寬表(Cassandra)、圖(Neo4j),加時序、搜尋、**向量(pgvector/Qdrant,RAG 用)**、欄式 OLAP(ClickHouse)、NewSQL(CockroachDB)。

**選型**:先分 **OLTP(行式關聯)vs OLAP(欄式倉儲)**,再看資料模型 + 一致性 + 規模 + 團隊/營運成本。**PostgreSQL 是最安全預設**(可擴充 JSONB/pgvector/TimescaleDB 一庫多用),撐不住再換;克制 polyglot persistence(每種庫都是持續成本)。

**追問**:CAP(金流強一致 vs 動態最終一致);向量庫連 [RAG](part28-llm-genai.md);OLTP/OLAP 對應行式/欄式儲存([T4](#t4-b-tree-與-lsm-tree-差在哪行式與欄式))。

---

# 操作篇(Python 存取資料庫)

## Q1.(必考)什麼是 SQL injection?怎麼防?

**考點**:DB-API([01-db-api](../chapters/15-database/11-db-api.md))

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

**考點**:sqlite3([02-sqlite3](../chapters/15-database/12-sqlite3.md))

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

**考點**:SQLAlchemy([03-sqlalchemy-core](../chapters/15-database/13-sqlalchemy-core.md) / [04-sqlalchemy-orm](../chapters/15-database/14-sqlalchemy-orm.md))

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

**考點**:連線池([05-connection-pool](../chapters/15-database/15-connection-pool.md))

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

**考點**:交易([06-transactions](../chapters/15-database/16-transactions.md))

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

**考點**:migration([07-migration](../chapters/15-database/17-migration.md))

**答**:migration 是「**schema 的版本控制**」——每次變更寫成**有版本、可 upgrade/downgrade 的腳本**,任何環境跑到最新得一致 schema。用 **Alembic**(`alembic_version` 表記錄目前版本、`down_revision` 串版本鏈)。

**零停機的破壞性變更**:**分階段**做——加(新欄)→ 遷移(填資料)→ 切換(程式改用新欄)→ 刪(舊欄)。別一步到位(舊程式會壞)。**大表 ALTER 會鎖表**要小心。

**追問**:`--autogenerate` 比對模型與 DB 差異,但**要 review**(改名、資料遷移偵測不準);migration 進 git;部署含 `alembic upgrade head`;**絕不手動改正式 schema**。

---

## Q7. Redis 為什麼快?cache-aside 模式?快取三大問題?

**考點**:Redis([08-redis](../chapters/15-database/18-redis.md))

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

**考點**:async DB([09-async-database](../chapters/15-database/19-async-database.md))

**答**:**同步 DB 查詢會阻塞 event loop**——所有並發請求停擺(同 [Part 09/14 的阻塞陷阱](part14-web.md#q9必考在-async-def-端點裡放阻塞操作會怎樣))。async 驅動(asyncpg)讓 DB I/O **非阻塞、可並發**。

**一路 async**:async 端點用 async 驅動 + `AsyncSession`、全程 await;否則用 `def` 端點(執行緒池)。

**追問**:

- **async 兩大陷阱?** → 不能隱式 lazy loading(要 eager,見 Q9);session **不能跨 task 共用**(非並發安全)。
- **async 永遠更快?** → **不是**。高並發 I/O bound 才值得;CPU bound/低並發/批次用同步。

---

## Q9.(必考)N+1 問題是什麼?怎麼解?

**考點**:N+1([10-n-plus-1](../chapters/15-database/20-n-plus-1.md))

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

**考點**:索引([11-indexing](../chapters/15-database/21-indexing.md))

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
