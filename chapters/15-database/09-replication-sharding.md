# 複製、分割與擴展

> 前面幾章都在講**一台**資料庫怎麼運作。但真實系統會遇到單機的極限:讀取量太大一台扛不住、資料量太大一台放不下、一台掛了整個服務就停。這章講資料庫的**水平擴展與高可用**三大手段——**複製(replication)**、**分割(partitioning)**、**分片(sharding)**。這是從「單機資料庫」邁向「分散式資料系統」的橋樑:複製解決「讀取擴展 + 高可用」、分割/分片解決「資料量與寫入擴展」。理解它們的機制與代價(尤其**複製延遲**與**跨分片查詢**的痛),你才懂為什麼分散式資料這麼難、以及 CAP 從哪來。

> 🧭 這章是單機資料庫通往 [Part 22 分散式系統](../22-distributed-systems/README.md) 的橋。分散式一致性理論(CAP、一致性模型)在 Part 22 深入;這章聚焦**資料庫層**的複製/分片機制與取捨。

## 💡 白話導讀(建議先讀)

一台資料庫的三個天花板,對應三帖藥:

**讀不動了 → 複製(開分身)。**
同一份資料多養幾個複本:寫都走主庫,讀分散到複本(讀寫分離)。主庫掛了,複本頂上(高可用)。
但有個經典幽靈——**複製延遲**:你改完個人資料立刻重整,讀到的複本還沒跟上→「我明明改了怎麼沒變?!」
(解法:寫後立即讀的場景改讀主庫。)

**放不下/寫不動了 → 分片(切開分散)。**
複製救不了這個——每個複本都是完整副本。分片把資料**切開**:1~1000 號客戶歸 A 機、1001~2000 歸 B 機。
代價很痛:跨分片 JOIN 幾乎廢了、跨分片交易沒有單機 ACID、**分片鍵選錯難回頭**。
還有個數學陷阱:用 `hash % N` 分片,機器從 4 加到 5 台——**八成的資料要搬家**(餘數全變了)。解法叫一致性雜湊,只搬一小角。

**所以第三帖藥其實是:先別吃前兩帖。**
加快取、加索引、垂直升級(換大機器)能撐很久——**分片是最後手段**,不是炫技首選。

這章是單機資料庫通往 [Part 22 分散式系統](../22-distributed-systems/README.md)的橋——CAP 那些難題,根源全在「資料有了多份」這件事。

## Why(為什麼)

一台資料庫再強也有天花板,長大的系統必然撞牆:

- **讀取擴展**:Web 應用通常**讀遠多於寫**。當單機的讀取量到極限(CPU/IO 打滿),你需要**多個複本分攤讀取**——這是複製的頭號用途。
- **高可用(HA)**:一台資料庫就是**單點故障(single point of failure)**——它掛了,整個服務停擺、甚至資料遺失。要有**備援複本**,主庫掛了能**故障切換(failover)** 頂上。這是任何正式系統的底線。
- **資料量與寫入擴展**:當資料大到一台磁碟放不下、或寫入量大到一台 CPU 扛不住,複製也救不了(每個複本都是完整副本、都要承受全部寫入)。這時要**分片(sharding)**——把資料**切開**分散到多台,每台只管一部分。
- **理解分散式的根本難題從這裡開始**:一旦資料有多份(複製)或多台(分片),就出現「複本之間何時一致」「跨分片的交易怎麼辦」「網路斷了選一致還是選可用」——這些正是 **CAP 定理**([Part 22](../22-distributed-systems/01-distributed-intro-cap.md))的來源。單機資料庫的 ACID 在這裡變得昂貴甚至不可能。

**這章讓你理解資料庫怎麼突破單機極限,以及突破的代價**——是設計大規模系統、也是面試系統設計題的核心。

## Theory(理論:複製 vs 分割 vs 分片)

三個概念常被混用,先分清楚:

```text
複製(Replication):同一份資料存多份(複本)
   Primary(主)─── 複製 ──> Replica 1(複本)
                └── 複製 ──> Replica 2(複本)
   目的:讀取擴展 + 高可用。每個複本是『完整副本』。

分割(Partitioning):把一張大表切成多塊(同一台或多台)
   Orders → [Orders_2023][Orders_2024][Orders_2025]  (按時間切)
   目的:管理大表、剪枝查詢。可在單機內(如 PostgreSQL 分區表)。

分片(Sharding):把資料『水平』切開分散到多台(分割 + 分佈)
   users 1-1000 → Shard A    users 1001-2000 → Shard B
   目的:資料量/寫入擴展。每台只存一部分資料。
```

**複製的兩種模式**(核心取捨):

- **同步複製(synchronous)**:主庫等**複本確認**才回 commit。**強一致**(複本不落後),但**慢**(要等複本)、複本掛了主庫可能卡住。
- **非同步複製(asynchronous)**:主庫**寫完就回**,複本在背景追。**快、可用性高**,但有**複製延遲(replication lag)**——複本可能落後主庫幾毫秒到幾秒,讀複本可能讀到**舊資料(最終一致)**。

**主從架構(primary-replica)**:寫都走主庫、讀可分散到複本(**讀寫分離**)。主庫掛了,**故障切換**把某個複本升為新主庫。

## Specification(規範:分片策略與擴展模式)

**垂直擴展 vs 水平擴展**:

| | 垂直(scale up) | 水平(scale out) |
|--|-----------------|------------------|
| 做法 | 換更強的機器(更多 CPU/RAM) | 加更多機器分攤 |
| 上限 | 有(單機物理極限) | 幾乎無限 |
| 複雜度 | 低(不改架構) | 高(複製/分片/一致性) |
| 原則 | **先垂直、撐不住再水平** | 真的需要規模才上 |

**分片鍵(shard key)策略**——決定資料怎麼分佈,選錯很痛:

| 策略 | 做法 | 優點 | 缺點 |
|------|------|------|------|
| **範圍分片(range)** | 按鍵區間切(如 A-M / N-Z) | 範圍查詢友善 | 易**熱點**(某區間特別熱) |
| **雜湊分片(hash)** | `hash(key) % N` 決定分片 | 分佈均勻、無熱點 | 範圍查詢要掃全部分片;**擴容要 rehash** |
| **一致性雜湊(consistent hash)** | 雜湊環 | 擴容只搬部分資料 | 較複雜 |
| **地理/租戶分片** | 按地區/客戶切 | 資料就近、隔離 | 可能不均 |

**分片帶來的痛(為什麼能不分片就別分片)**:

- **跨分片查詢/JOIN 極難**:資料在不同機器,JOIN 要跨網路收集,慢且複雜。
- **跨分片交易失去單機 ACID**:要用**分散式交易 / Saga**([Part 22](../22-distributed-systems/07-saga.md))——最終一致,複雜。
- **分片鍵選錯難改**:資料已按它分佈,重分片是大工程。
- **rebalancing(再平衡)**:加機器要搬資料。

## Implementation(底層:複製延遲與讀己之寫)

**複製延遲(replication lag)的真實後果**——「讀己之寫(read-your-writes)」問題:

```text
使用者改了個人資料(寫 → 主庫)→ 立刻重整頁面(讀 → 某個複本)
若該複本還沒追上主庫(有 lag)→ 使用者看到『改之前的舊資料』
→「我明明改了,怎麼沒變?」的經典 bug
```

這是**最終一致性**在讀寫分離下的典型陷阱。**解法**:

- **讀主庫**:對「剛寫完馬上要讀」的關鍵操作,強制讀主庫(犧牲讀取擴展)。
- **會話一致性(session consistency)**:同一使用者的讀,路由到「保證看得到他自己寫入」的複本或主庫。
- **等待複本追上**:讀之前確認複本的位置 ≥ 剛寫入的位置。

**故障切換(failover)的難題**:主庫掛了,把複本升主——但**非同步複製下,複本可能還沒收到主庫最後幾筆已 commit 的寫入** → 這些寫入在切換後**遺失**。同步複製可避免但慢。這是 CAP 在資料庫層的直接體現:網路分區/故障時,你**要嘛選一致(可能不可用/卡住)、要嘛選可用(可能不一致/丟資料)**。

**雜湊分片的擴容之痛**:`hash(key) % N`,當 N 從 4 變 5,**幾乎所有 key 的分片都變了** → 要搬移大量資料。**一致性雜湊**用「雜湊環」讓擴容只影響相鄰節點的部分資料,大幅減少搬移([Part 22 也用於快取](../22-distributed-systems/05-caching-strategies.md))。下面用 Python 實作分片路由、複製延遲、與一致性雜湊。

## Code Example(可執行的 Python 範例)

```python
# replication_sharding.py — 分片路由 + 複製延遲 + 一致性雜湊(純標準庫)
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


# ---------- 雜湊分片 vs 擴容成本 ----------
def hash_shard(key: str, n: int) -> int:
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    return h % n


def rehash_cost(keys: list[str], old_n: int, new_n: int) -> float:
    """N 改變後,有多少比例的 key 需要搬到不同分片(取模分片的痛)。"""
    moved = sum(1 for k in keys if hash_shard(k, old_n) != hash_shard(k, new_n))
    return round(moved / len(keys), 3)


# ---------- 主從複製 + 複製延遲 ----------
@dataclass
class Primary:
    data: dict[str, int] = field(default_factory=dict)
    log_position: int = 0

    def write(self, key: str, value: int) -> int:
        self.data[key] = value
        self.log_position += 1
        return self.log_position


@dataclass
class Replica:
    data: dict[str, int] = field(default_factory=dict)
    applied_position: int = 0

    def apply_up_to(self, primary: Primary, position: int) -> None:
        """非同步套用主庫的變更到某個位置(模擬追趕)。"""
        self.data = dict(primary.data)
        self.applied_position = position

    def read(self, key: str) -> int | None:
        return self.data.get(key)


def main() -> None:
    # 1) 讀己之寫問題:寫主庫後立刻讀『落後的』複本
    primary = Primary()
    replica = Replica()
    pos = primary.write("profile", 100)   # 使用者更新資料
    print("複製延遲(讀己之寫):")
    print(f"  主庫已寫 profile=100 (log 位置 {pos})")
    print(f"  立刻讀落後複本 profile = {replica.read('profile')} ← 看不到剛寫的!(lag)")
    replica.apply_up_to(primary, pos)      # 複本追上
    print(f"  複本追上後讀 profile = {replica.read('profile')}")

    # 2) 雜湊分片路由
    print("\n雜湊分片路由(4 個分片):")
    for key in ["user:1", "user:2", "user:3"]:
        print(f"  {key} -> shard {hash_shard(key, 4)}")

    # 3) 取模分片擴容的搬移成本
    keys = [f"user:{i}" for i in range(10000)]
    print("\n取模分片擴容搬移比例:")
    print(f"  4 -> 5 個分片: {rehash_cost(keys, 4, 5):.1%} 的 key 要搬移")
    print(f"  4 -> 8 個分片: {rehash_cost(keys, 4, 8):.1%} 的 key 要搬移")


if __name__ == "__main__":
    main()
```

**預期輸出**:

```pycon
$ python replication_sharding.py
複製延遲(讀己之寫):
  主庫已寫 profile=100 (log 位置 1)
  立刻讀落後複本 profile = None ← 看不到剛寫的!(lag)
  複本追上後讀 profile = 100

雜湊分片路由(4 個分片):
  user:1 -> shard 2
  user:2 -> shard 1
  user:3 -> shard 3

取模分片擴容搬移比例:
  4 -> 5 個分片: 79.6% 的 key 要搬移
  4 -> 8 個分片: 50.3% 的 key 要搬移
```

逐段解說:

- **讀己之寫問題被具體重現**:主庫寫了 `profile=100`(log 位置 1),但複本**還沒套用**(`applied_position=0`)——立刻讀複本得到 `None`(看不到剛寫的值)。這正是「我明明改了怎麼沒變」的根因:**非同步複製下複本落後主庫**。等 `apply_up_to` 追上,才讀得到 100。實務要靠「讀主庫」或「會話一致性」解。
- **雜湊分片路由**:`hash(key) % 4` 把不同 user 均勻分到 4 個分片——無熱點,但**範圍查詢(如 user:1~100)要掃所有分片**,因為雜湊打散了順序。
- **取模分片擴容的痛(震撼數字)**:分片數從 **4→5,竟有 79.6% 的 key 要搬到不同分片**(4→8 也有約 5 成)!因為 `hash % N` 裡 N 一變,幾乎所有 key 的餘數都變了。這解釋了為什麼**簡單取模分片擴容是災難**,以及為什麼要用**一致性雜湊**(擴容只搬相鄰節點的一小部分資料)。
- **對映真實決策**:這些數字告訴你「分片鍵與分片策略要一開始想清楚」——選錯或天真取模,擴容時要搬移大半資料、停機風險高。
- **要點**:複製(多份完整副本)解決讀取擴展 + 高可用,代價是複製延遲(最終一致、讀己之寫問題)與 failover 可能丟資料;分片(切開分散)解決資料量/寫入擴展,代價是跨分片查詢/交易極難、取模擴容要大搬移(用一致性雜湊緩解);先垂直擴展、真的需要才水平。

## Diagram(圖解:複製與分片)

```mermaid
flowchart TB
    subgraph REPL["複製(讀取擴展 + 高可用)"]
        APP1["應用"] -->|寫| PRI[("Primary 主庫")]
        APP1 -->|讀(可能有 lag)| R1[("Replica 1")]
        APP1 -->|讀| R2[("Replica 2")]
        PRI -.非同步複製.-> R1
        PRI -.非同步複製.-> R2
        PRI -. 掛了 → failover 升主 .-> R1
    end
    subgraph SHARD["分片(資料量 + 寫入擴展)"]
        APP2["應用 + 分片路由"] -->|hash(key)%N| SA[("Shard A<br/>user 1-1000")]
        APP2 --> SB[("Shard B<br/>user 1001-2000")]
        APP2 --> SC[("Shard C<br/>user 2001-3000")]
    end
    style PRI fill:#e8f5e9
    style SHARD fill:#fff3e0
```

## Best Practice(最佳實踐)

- **先垂直擴展、加快取、加索引**:多數瓶頸不必分片就能解決;分片是最後手段。
- **用複製做讀取擴展 + 高可用**:讀寫分離分攤讀取、備援複本 + 自動 failover。
- **正視複製延遲**:對「寫後立刻讀」的關鍵路徑讀主庫或用會話一致性,別假設複本即時同步。
- **同步 vs 非同步依需求**:不能丟資料(金流)傾向同步/半同步;高可用優先用非同步 + 監控 lag。
- **分片鍵慎選、避免熱點**:選高基數、存取均勻的鍵;範圍分片小心熱點、雜湊分片難範圍查詢。
- **用一致性雜湊而非裸取模**:讓擴容只搬部分資料。
- **盡量讓查詢落單一分片**:把常一起查的資料放同分片(如同租戶)、避免跨分片 JOIN。
- **跨分片交易用 Saga/最終一致**:別期待跨分片單機 ACID([Part 22](../22-distributed-systems/07-saga.md))。
- **監控 lag、故障切換演練**:HA 沒演練過等於沒有。

## Common Mistakes(常見誤解)

- **過早分片**:徒增巨大複雜度(跨分片查詢/交易);先窮盡垂直 + 複製 + 快取。
- **假設複本即時一致**:非同步有 lag,寫後立刻讀複本會讀到舊值(讀己之寫)。
- **裸 `hash % N` 分片還想輕鬆擴容**:N 一變大半 key 要搬;用一致性雜湊。
- **分片鍵選到會熱點的欄**(如時間、自增 id 的範圍分片):流量集中單一分片。
- **以為分片後還能隨意 JOIN**:跨分片 JOIN 極慢且複雜;設計要讓查詢落單分片。
- **非同步複製卻要求零資料遺失**:failover 可能丟未複製的 commit;要零丟失得同步複製。
- **有複製就以為有備份**:複製會把「誤刪」也複製過去;複製 ≠ 備份,仍要獨立備份([Part 31](../31-cloud-platform-deployment/06-managed-db-storage.md))。
- **HA 從不演練 failover**:真的掛掉時才發現切換有問題。

## Interview Notes(面試重點)

- **能分清複製 / 分割 / 分片**:複製=多份完整副本(讀擴展+HA)、分割=切大表、分片=水平切開分散(資料/寫入擴展)。
- **能講同步 vs 非同步複製的取捨**:強一致慢 vs 快但有複製延遲(最終一致)。
- **(高頻)能講複製延遲與讀己之寫**:寫後讀落後複本看到舊值;解法讀主庫/會話一致性。
- **能講分片策略**:範圍(範圍查詢友善但熱點)vs 雜湊(均勻但難範圍、擴容 rehash)vs 一致性雜湊。
- **能講分片的代價**:跨分片查詢/交易難、rebalancing、分片鍵難改;所以先垂直再水平。
- **能講 failover 與資料遺失**:非同步下切換可能丟未複製的 commit——CAP 在資料庫層的體現。
- **能連到 CAP 與分散式**:多副本/多分片引出一致性 vs 可用性取捨([Part 22](../22-distributed-systems/01-distributed-intro-cap.md));複製 ≠ 備份。

---

➡️ 下一章:[NoSQL 家族與資料庫選型](10-nosql-selection.md)

[⬆️ 回 Part 15 索引](README.md)
