# 託管資料庫與物件儲存

> 前幾章的容器/函式都是**無狀態**的——那**狀態放哪?** 答案是雲的**託管資料庫(managed database)** 與**物件儲存(object storage)**。你不自己架 PostgreSQL、不自己買硬碟:用 AWS **RDS** / GCP **Cloud SQL** 存關聯式資料,用 **S3** / **Cloud Storage(GCS)** 存檔案。雲負責高可用、備份、修補、擴容。這章講清楚兩者的定位與取捨(為何 DB 不縮到零、物件儲存為何幾乎無限便宜)、AWS↔GCP 對照、連線與安全,並用 Python 實作儲存選型與成本估算。

## Why(為什麼)

無狀態運算(容器/函式)必須把狀態**外置**——但為什麼是**託管** DB/儲存,而不是自己架?

- **自架資料庫是重擔且高風險**:高可用(主從/故障切換)、備份與還原、版本升級、安全修補、擴容、監控——**搞砸就是資料遺失或外洩**。託管服務把這些接手,你專注 schema 與查詢。
- **運算與儲存要分離**:容器/函式**隨時被建銷、多份、縮到零**,絕不能把資料存在它們的本機磁碟。狀態要放在**獨立、持久、可被多實例共享**的地方——這正是託管 DB / 物件儲存的角色。
- **不同資料要用對的儲存**:結構化交易資料(使用者、訂單)→ 關聯式 DB;大檔案(圖片、影片、備份、資料湖)→ 物件儲存;快取/session → Redis;分析 → 資料倉儲。**用錯儲存又貴又難用**(如把圖片塞進 DB)。
- **成本模型差異巨大**:物件儲存**極便宜、近乎無限**(按 GB 儲存 + 傳輸);DB **相對貴**(常駐實例 + 儲存 + IOPS)。理解差異才能省錢——把大檔案放物件儲存、DB 只存結構化資料與**指向檔案的 URL**。

**核心心法**:**運算無狀態、狀態放對地方**。task-api 的任務資料進 Cloud SQL/RDS、附件進 GCS/S3、熱資料快取進 Redis。這章建立這套心智。

## Theory(理論:三類狀態儲存)

雲上狀態儲存大致三類,各有定位:

```text
┌─ 關聯式 DB(RDS / Cloud SQL)──────────────────────────┐
│  結構化、交易(ACID)、SQL、關聯查詢                     │
│  用於:核心業務資料(users, tasks, orders)             │
│  特性:常駐實例(不縮到零)、相對貴、需連線池            │
├─ 物件儲存(S3 / Cloud Storage)────────────────────────┤
│  非結構化大檔、HTTP 存取、近乎無限、極便宜               │
│  用於:圖片/影片/備份/日誌/資料湖/靜態網站              │
│  特性:按 GB + 請求計費、高耐久(11 個 9)、非檔案系統   │
├─ 記憶體快取 / NoSQL(ElastiCache/Memorystore, DynamoDB/Firestore)
│  快取、session、高吞吐 KV、彈性 schema                  │
│  用於:熱資料快取、session、計數器、事件流              │
└────────────────────────────────────────────────────────┘
```

**關聯式 DB 為何「不縮到零」**:資料庫要**維持連線、快取、一致性狀態**——它是**有狀態的常駐服務**,不像無狀態容器能隨意起停。所以雲 DB 是**按實例常駐計費**(近年有 serverless DB 如 Aurora Serverless 能自動伸縮,但仍不是真正「零成本閒置」)。這是「運算能縮到零、資料層不能」的根本原因——狀態需要一個**穩定的家**。

**物件儲存為何這麼便宜又耐久**:它不是檔案系統,而是**扁平的 key→物件**映射(bucket/key),透過 HTTP API 存取。這種簡單模型讓雲能**大規模分散、多副本複製**——換來**極高耐久性(S3 標稱 99.999999999% / 11 個 9)** 與**近乎無限容量**,單位成本極低。代價:**沒有檔案系統語意**(不能隨機改寫、沒有真正的目錄,「資料夾」只是 key 前綴)。

## Specification(規範:AWS ↔ GCP 儲存對照)

| 類別 | AWS | GCP | 用途 |
|------|-----|-----|------|
| **關聯式 DB** | RDS(PostgreSQL/MySQL…) | Cloud SQL | 核心交易資料 |
| **Serverless 關聯** | Aurora Serverless | Cloud SQL(+ AlloyDB) | 自動伸縮的關聯 DB |
| **NoSQL 文件** | DynamoDB | Firestore | 彈性 schema、高吞吐 KV |
| **NoSQL 寬表** | DynamoDB | Bigtable | 超大規模時序/事件 |
| **物件儲存** | S3 | Cloud Storage(GCS) | 檔案/備份/資料湖 |
| **記憶體快取** | ElastiCache(Redis) | Memorystore(Redis) | 快取/session |
| **資料倉儲** | Redshift | BigQuery | 分析 OLAP |

**物件儲存的儲存類別(storage class)**——按存取頻率選,越冷越便宜:

| 存取頻率 | AWS S3 | GCP GCS |
|----------|--------|---------|
| 頻繁 | Standard | Standard |
| 偶爾 | Standard-IA | Nearline |
| 罕見 | Glacier Instant | Coldline |
| 歸檔 | Glacier Deep Archive | Archive |

**連線字串示意**(關聯式 DB,兩雲都是標準 PostgreSQL/MySQL 協定 → **可攜**):

```text
postgresql://user:pass@task-db.xxxx.rds.amazonaws.com:5432/tasks   # RDS
postgresql://user:pass@/tasks?host=/cloudsql/proj:region:instance  # Cloud SQL(socket)
```

## Implementation(底層:連線池、預簽 URL、備份)

**連線池(connection pooling)——DB 不可省的一環**:資料庫連線**昂貴**(建立要 TCP + TLS + 認證),且 DB 有**最大連線數上限**。無伺服器/多實例環境下,每個實例都開一堆連線會**很快耗盡 DB 連線**。解法:

- **應用層連線池**:如 SQLAlchemy 的 pool,重用連線([Part 15 資料庫](../15-database/README.md))。
- **外部 pooler**:PgBouncer、RDS Proxy、Cloud SQL 的連線管理——在 DB 前擋一層,收斂連線數。**Serverless(Lambda/Cloud Run 縮放到很多實例)尤其需要**,否則瞬間擴容會打爆 DB。

**物件儲存的預簽 URL(presigned URL)——關鍵模式**:讓客戶端**直接**上傳/下載物件,**不經過你的伺服器**:

```python
# 概念:後端產生有時效的簽名 URL,客戶端拿它直接對 S3/GCS 上傳
url = s3.generate_presigned_url("put_object",
        Params={"Bucket": "uploads", "Key": "u123/photo.jpg"},
        ExpiresIn=300)  # 5 分鐘有效
# 客戶端: PUT <url> with file bytes  → 直傳,不佔用你的伺服器頻寬
```

**為何重要**:大檔案若都經過你的容器中轉,會**吃滿頻寬與記憶體**、拖慢服務;預簽 URL 讓儲存服務直接處理傳輸,你的後端只**授權**(產生短時效簽名),不搬資料。這是雲上處理檔案上傳/下載的標準做法。

**備份與高可用(託管的核心價值)**:託管 DB 提供**自動備份、時間點還原(PITR)、多可用區(Multi-AZ)故障切換、讀取複本**——這些自架要花大力氣。你要做的是**開啟並驗證**這些功能(別假設預設全開),並定期**演練還原**(沒驗證過的備份等於沒備份)。下面用 Python 實作儲存選型與成本估算。

## Code Example(可執行的 Python 範例)

```python
# storage.py — 儲存選型 + 物件儲存 vs DB 成本估算(純標準庫)
from __future__ import annotations

from dataclasses import dataclass


def choose_storage(structured: bool, transactional: bool,
                   large_binary: bool, needs_cache: bool) -> str:
    """依資料特性選儲存。"""
    if large_binary:
        return "物件儲存(S3 / Cloud Storage)- 大檔:DB 只存 URL"
    if needs_cache:
        return "記憶體快取(ElastiCache / Memorystore)- 熱資料/session"
    if structured and transactional:
        return "關聯式 DB(RDS / Cloud SQL)- 交易一致性"
    if structured:
        return "關聯式 DB 或 NoSQL,依查詢型態"
    return "NoSQL(DynamoDB / Firestore)- 彈性 schema"


@dataclass
class StorageCost:
    per_gb_month: float


def object_storage_cost(gb: float, cost: StorageCost) -> float:
    return round(gb * cost.per_gb_month, 2)


def db_monthly_cost(instance_usd_per_hour: float, storage_gb: float,
                    storage_per_gb: float) -> float:
    """DB 常駐:實例費(24x30 小時)+ 儲存費。"""
    instance = instance_usd_per_hour * 24 * 30
    storage = storage_gb * storage_per_gb
    return round(instance + storage, 2)


def main() -> None:
    print("儲存選型:")
    cases = [
        ("使用者/任務資料", True, True, False, False),
        ("使用者上傳的圖片", False, False, True, False),
        ("熱門排行榜快取", False, False, False, True),
        ("事件日誌(彈性欄位)", False, False, False, False),
    ]
    for name, s, t, b, c in cases:
        print(f"  {name}: {choose_storage(s, t, b, c)}")

    print("\n成本對照:存 1000GB 大檔")
    obj = object_storage_cost(1000, StorageCost(per_gb_month=0.023))  # S3 Standard 近似
    print(f"  放物件儲存: ${obj}/月")
    # 若硬塞進 DB(小實例 + 1000GB 儲存)
    db = db_monthly_cost(instance_usd_per_hour=0.10, storage_gb=1000,
                         storage_per_gb=0.115)  # DB 儲存單價較高
    print(f"  硬塞進 DB:  ${db}/月(實例常駐 + 昂貴儲存)")


if __name__ == "__main__":
    main()
```

**預期輸出**:

```pycon
$ python storage.py
儲存選型:
  使用者/任務資料: 關聯式 DB(RDS / Cloud SQL)- 交易一致性
  使用者上傳的圖片: 物件儲存(S3 / Cloud Storage)- 大檔:DB 只存 URL
  熱門排行榜快取: 記憶體快取(ElastiCache / Memorystore)- 熱資料/session
  事件日誌(彈性欄位): NoSQL(DynamoDB / Firestore)- 彈性 schema

成本對照:存 1000GB 大檔
  放物件儲存: $23.0/月
  硬塞進 DB:  $187.0/月(實例常駐 + 昂貴儲存)
```

逐段解說:

- **`choose_storage` 的優先序**:先判**大檔**(一律物件儲存,DB 只存指向它的 URL)→ **快取需求** → **結構化 + 交易**(關聯式 DB)→ 其餘彈性 schema 走 NoSQL。**「大檔進物件儲存、結構化進 DB」是最常見且最省的分工**。
- **成本對照的震撼**:同樣 1000GB,放物件儲存 **$23/月**,硬塞進 DB **$187/月**——**差 8 倍**。原因:DB 是**常駐實例 + 昂貴的區塊儲存(要支撐 IOPS/交易)**,物件儲存是**便宜的分散式儲存**。這數字解釋了為什麼**大檔絕不塞 DB**——DB 存 metadata + URL,檔案本體進物件儲存。
- **實務落地**:task-api 的任務進 Cloud SQL、附件進 GCS(DB 存附件的 GCS key)、熱查詢快取進 Redis——各司其職。
- **要點**:運算無狀態、狀態放對地方;關聯式 DB 存結構化交易資料(常駐、不縮到零、需連線池);物件儲存存大檔(極便宜、耐久、用預簽 URL 直傳);快取/NoSQL 各有場景。

## Diagram(圖解:運算與狀態分離)

```mermaid
flowchart TB
    subgraph COMPUTE["無狀態運算(容器/函式,可縮到零)"]
        APP["task-api 實例 x N"]
    end
    APP -->|結構化交易資料| DB[("關聯式 DB<br/>RDS / Cloud SQL<br/>常駐 + 連線池")]
    APP -->|熱資料/session| CACHE[("Redis<br/>ElastiCache / Memorystore")]
    APP -->|授權: 產生預簽 URL| OBJ[("物件儲存<br/>S3 / GCS")]
    CLIENT["客戶端"] -.預簽 URL 直傳大檔.-> OBJ
    DB -.只存 URL/metadata.-> OBJ
    style COMPUTE fill:#e3f2fd
    style DB fill:#fff3e0
    style OBJ fill:#e8f5e9
```

## Best Practice(最佳實踐)

- **運算無狀態、狀態外置**:資料進託管 DB、檔案進物件儲存、快取/session 進 Redis;容器磁碟只當暫存。
- **大檔進物件儲存、DB 只存 URL/metadata**:成本差數倍,且 DB 不被大 blob 拖累。
- **用預簽 URL 直傳/直下**:大檔不經你的伺服器中轉,省頻寬與記憶體。
- **一定要用連線池 / pooler**:無伺服器多實例會打爆 DB 連線;用 pool + RDS Proxy/PgBouncer。
- **開啟並驗證備份/PITR/Multi-AZ**:別假設預設全開;定期演練還原。
- **選對儲存類別**:冷資料用 Nearline/Glacier 省錢;設生命週期規則自動降級。
- **DB 私有、不對公網**:放私有子網,只讓應用/pooler 連([ch07 網路](07-secrets-config-network.md))。
- **憑證用密鑰管理 + IAM 資料庫認證**:別把 DB 密碼寫死([ch07](07-secrets-config-network.md))。
- **善用標準協定保可攜**:用標準 PostgreSQL/MySQL,降低換雲成本。

## Common Mistakes(常見誤解)

- **把大檔塞進資料庫**:又貴又慢又難備份;檔案進物件儲存,DB 存 URL。
- **狀態存容器本機磁碟**:實例被銷毀就遺失、多實例不一致。
- **無伺服器不用連線池**:瞬間擴容開爆 DB 連線;用 pooler。
- **以為物件儲存是檔案系統**:不能隨機改寫、沒有真目錄(前綴模擬);大檔改寫要整份覆蓋。
- **大檔經伺服器中轉**:吃滿頻寬/記憶體;用預簽 URL 直傳。
- **沒驗證備份**:沒演練過還原 = 沒有備份;定期演練。
- **DB 直接暴露公網**:攻擊面大;放私有網路。
- **DB 密碼寫死在程式/映像**:外洩來源;用密鑰管理([ch07](07-secrets-config-network.md))。
- **期待關聯式 DB 縮到零省錢**:它是常駐有狀態服務;省錢靠選規格/serverless DB,而非縮到零。

## Interview Notes(面試重點)

- **能講運算/狀態分離**:無狀態容器/函式 + 託管 DB/物件儲存/快取,狀態放對地方。
- **能講為何 DB 不縮到零、物件儲存為何便宜耐久**:DB 是常駐有狀態服務;物件儲存是扁平 key→物件、多副本、11 個 9。
- **能講大檔為何進物件儲存**:成本差數倍、DB 只存 URL/metadata。
- **能講預簽 URL**:客戶端直傳/直下,不經伺服器中轉。
- **能講連線池的必要**:DB 連線昂貴且有上限,無伺服器多實例要用 pooler(RDS Proxy/PgBouncer)。
- **能對照 AWS/GCP**:RDS/Cloud SQL、S3/GCS、DynamoDB/Firestore、ElastiCache/Memorystore、Redshift/BigQuery。
- **能講備份/HA**:自動備份、PITR、Multi-AZ、讀取複本;要開啟並演練還原。

---

➡️ 下一章:[密鑰、設定與網路](07-secrets-config-network.md)

[⬆️ 回 Part 31 索引](README.md)
