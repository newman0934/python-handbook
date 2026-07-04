# Part 15：資料庫 Database

> 從**資料庫引擎的內部原理**(關聯模型、SQL 語意、正規化、儲存/索引/優化器、交易並發、WAL、複製分片、NoSQL 選型)一路到**用 Python 實際操作資料庫**(DB-API、SQLAlchemy、連線池、交易、migration、Redis、async、N+1、索引優化)。前半懂「資料庫是什麼、怎麼運作」,後半懂「怎麼用」。

本 Part 分兩大區塊,依「**由底層往上**」順序閱讀:先懂引擎原理,再學 Python 操作。

## 第一區塊:資料庫原理與內部機制(理論)

理解「資料庫本身如何運作」——**廠商中立、跨所有 SQL 資料庫通用**。範例以純標準庫模擬引擎機制(關聯代數、B+tree、MVCC、WAL…),可離線執行與測試。

| 章 | 標題 | 重點 |
|----|------|------|
| 01 | [關聯式模型與關聯代數](01-relational-model.md) | 關聯/鍵/關聯代數,SQL 的數學骨架 |
| 02 | [SQL 語言深入](02-sql-language.md) | 邏輯處理順序、**NULL 三值邏輯**、JOIN 語意 |
| 03 | [正規化與資料建模](03-normalization.md) | 函數相依、1NF→BCNF、反正規化取捨 |
| 04 | [儲存引擎與磁碟結構](04-storage-engine.md) | 頁/buffer pool、行式 vs 欄式、B-tree vs LSM |
| 05 | [索引內部原理](05-index-internals.md) | **B+tree**、最左前綴、覆蓋索引、聚簇 |
| 06 | [查詢處理與優化器](06-query-processing.md) | 三種 JOIN 演算法、選擇性、EXPLAIN |
| 07 | [交易與並發控制](07-transactions-concurrency.md) | 隔離級別、異常、**鎖 vs MVCC**、死鎖 |
| 08 | [WAL 與故障恢復](08-wal-recovery.md) | 預寫式日誌、redo/undo、checkpoint |
| 09 | [複製、分割與擴展](09-replication-sharding.md) | 主從複製、複製延遲、分片策略 |
| 10 | [NoSQL 家族與資料庫選型](10-nosql-selection.md) | 文件/KV/寬表/圖/向量、OLTP/OLAP、選型 |

## 第二區塊:用 Python 操作資料庫(實作)

把上面的原理落到 Python 實務——連線、ORM、交易、遷移、快取、async 與效能。

| 章 | 標題 |
|----|------|
| 11 | [DB-API 規範](11-db-api.md) |
| 12 | [sqlite3](12-sqlite3.md) |
| 13 | [SQLAlchemy Core](13-sqlalchemy-core.md) |
| 14 | [SQLAlchemy ORM](14-sqlalchemy-orm.md) |
| 15 | [連線池](15-connection-pool.md) |
| 16 | [transaction 交易](16-transactions.md) |
| 17 | [migration 與 Alembic](17-migration.md) |
| 18 | [Redis 與快取](18-redis.md) |
| 19 | [async 資料庫存取 (SQLAlchemy async / asyncpg)](19-async-database.md) |
| 20 | [N+1 問題與 eager / lazy loading](20-n-plus-1.md) |
| 21 | [索引與查詢優化基礎](21-indexing.md) |

> 🔗 兩區呼應:原理篇 [ch05 索引內部原理](05-index-internals.md) ↔ 實作篇 [ch21 索引與查詢優化基礎](21-indexing.md);原理篇 [ch07 交易與並發控制](07-transactions-concurrency.md) ↔ 實作篇 [ch16 transaction 交易](16-transactions.md)。原理篇講「引擎為什麼這樣」,實作篇講「Python 怎麼用」。

---

⬅️ 上一 Part：[Web 開發](../14-web/README.md)　｜　➡️ 下一 Part：[架構與設計](../16-architecture/README.md)

[⬆️ 回章節總覽](../README.md)
