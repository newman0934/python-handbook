# Part 22 面試題:分散式系統

> 對應 [Part 22 分散式系統](../chapters/22-distributed-systems/README.md)。資深/系統設計核心——CAP、一致性、分散式鎖、訊息佇列、冪等、Saga。

---

## Q1.(必考)CAP 定理是什麼?「三選二」的說法對嗎?

**考點**:CAP([01-distributed-intro-cap](../chapters/22-distributed-systems/01-distributed-intro-cap.md))

**答**:CAP——分散式系統在 **C(一致性)、A(可用性)、P(分區容錯)** 中最多同時滿足兩者。

**「三選二」是常見誤解**!正確理解:**P(網路分區)是必需品**(網路一定會斷),所以真正的取捨是——**當分區發生時,C 和 A 二選一**(正常時可兼得):

- **分區時選 C**:拒絕服務(寧可不回應也不給錯資料)→ **CP**(ZooKeeper/etcd/傳統 DB)。
- **分區時選 A**:繼續服務(可能給舊資料)→ **AP**(Cassandra/DynamoDB/DNS)。

**為何分區下無法兼得**:分區把節點切成兩半、資訊無法傳遞——要嘛拒絕(保 C 犧牲 A)、要嘛各自服務(保 A 犧牲 C)。

**追問**:可調一致性與 **Quorum(W+R>N 給強一致)**(見 Q2)。

---

## Q2. 一致性有哪些等級?Quorum(W+R>N)為什麼保證強一致?

**考點**:一致性模型([02-consistency-models](../chapters/22-distributed-systems/02-consistency-models.md))

**答**:一致性光譜(由強到弱):**線性一致 → 因果 → 會話(讀己所寫/單調讀)→ 最終一致**——越強代價越高(延遲/可用性)。

**Quorum**:N 個副本,寫要 W 個確認、讀要 R 個。**W + R > N 保證強一致**——因為讀集和寫集**必有交集**(鴿籠原理),讀到的至少一個副本有最新寫入:

```text
N=3, W=2, R=2 → W+R=4 > 3 → 讀集與寫集必有交集 → 強一致
```

**追問**:最終一致的**衝突解決**——LWW(last-write-wins,有丟更新風險)、向量時鐘、CRDT;**會話一致性(讀己所寫)** 是實用便宜的折衷;**依業務選**(金融強一致、社群最終一致),別無腦全強一致。

---

## Q3.(必考)分散式鎖用 Redis 的「鎖 + TTL」有什麼致命陷阱?fencing token 怎麼解?

**考點**:分散式鎖([03-distributed-lock](../chapters/22-distributed-systems/03-distributed-lock.md))

**答**:分散式鎖三要求:**互斥、無死鎖(需 TTL)、容錯**。

**「鎖 + TTL」的致命陷阱**:持有者拿到鎖後**因 GC/網路延遲卡住**,超過 TTL → **鎖自動過期** → 另一個人拿到鎖 → **兩人同時持鎖**(互斥被破壞),之後卡住的那個醒來還以為自己持鎖繼續操作 → 資料損毀。

**fencing token 是根本解**:每次發鎖給一個**單調遞增的 token**,資源端**只接受 token 更大的操作**——卡住的舊持有者醒來時 token 較小,操作被拒絕:

```text
Client A 拿鎖(token=33)→ 卡住
鎖過期,Client B 拿鎖(token=34)→ 寫入(資源記住 34)
A 醒來,用 token=33 寫入 → 資源拒絕(33 < 34)!
```

把安全性從「**持有者自己判斷**」轉到「**資源端的單調檢查**」。

**追問**:Redis 鎖細節(`SET NX EX`、釋放要驗證持有者身分、用 Lua 保原子);Redlock 及其爭議,fencing token 更根本。

---

## Q4. Kafka 和 RabbitMQ 差在哪?三種投遞語意?

**考點**:訊息佇列([04-message-queue](../chapters/22-distributed-systems/04-message-queue.md))

**答**:

| | Kafka | RabbitMQ |
|---|-------|----------|
| 哲學 | **分散式日誌**(訊息保留、可重播) | **訊息佇列**(消費即刪) |
| 特性 | 高吞吐、offset、可重播 | 靈活路由 |
| 適用 | 事件流、日誌、串流處理 | 任務佇列、複雜路由 |

**三種投遞語意**:

- **at-most-once**:丟了不重(可接受漏)。
- **at-least-once**:不丟但**可能重複**(**最常用**)。
- **exactly-once**:最難。

**實務:at-least-once + 消費者冪等**(見 Q6)——效果上達成 exactly-once。

**追問**:offset 提交時機決定 at-least/at-most(先處理後提交 = at-least);Kafka 的 **partition(保序 + 並行)+ consumer group(分工)**,**同 key 同 partition 保序**;消費者必須冪等、死信佇列、監控 consumer lag。

---

## Q5.(必考)什麼是冪等?為什麼分散式系統一定會有重複?怎麼實作?

**考點**:冪等([06-idempotency](../chapters/22-distributed-systems/06-idempotency.md))

**答**:**冪等**——執行一次和多次結果**相同**。分散式**無法避免重複**:客戶端發請求後**逾時**,它不知道「伺服器有沒有處理成功」——重試可能導致**重複執行**(如重複扣款)。

- **天生冪等**:GET、PUT(設絕對值)、DELETE。
- **不冪等**:POST(建立)、`balance += 100`(相對變化)、append。

**idempotency key 機制**:客戶端帶一個**唯一鍵**,伺服器**原子地「檢查 + 記錄」**——這個 key 處理過就**回放之前的結果**(不重做):

```python
if key_exists(idem_key):
    return cached_result(idem_key)    # 重複請求,回放
result = process()
store(idem_key, result)                # 原子(DB 唯一約束)
```

**「at-least-once + 冪等 = 效果上 exactly-once」**——分散式達成恰好一次的**標準做法**。

**追問**:「檢查 + 記錄」的**原子性**至關重要(用 DB 唯一約束,否則兩個並發請求都通過檢查)。

---

## Q6. 快取的讀寫策略?為什麼「先更新 DB 後刪快取」而非更新快取?

**考點**:快取策略([05-caching-strategies](../chapters/22-distributed-systems/05-caching-strategies.md))

**答**:讀寫策略:**Cache-Aside**(最常用)、Read-Through、Write-Through、Write-Back、Write-Around。

**「失效優於更新」+「先更新 DB 後刪快取」**:更新 DB 後**刪除**快取(而非寫入新值)——因為兩個並發的「更新快取」可能亂序(舊值後寫,覆蓋新值,產生髒資料);**刪除**讓下次讀時重建,較安全。

**追問**:TTL 兜底(最終一致的安全網);三大經典問題——**穿透**(空值/布隆過濾器)、**擊穿**(互斥重建熱點)、**雪崩**(TTL 加抖動)(同 [Part 15](part15-database.md#q7-redis-為什麼快cache-aside-模式快取三大問題));快取與 DB 是**最終一致**,強一致代價高。

---

## Q7. Saga 是什麼?補償和 rollback 差在哪?

**考點**:Saga([07-saga](../chapters/22-distributed-systems/07-saga.md))

**答**:微服務因 **database-per-service** **不能用單一 ACID 交易**(跨服務),而 2PC(兩階段提交)有阻塞、單點、可用性差的缺點。**Saga** 是替代:**一連串本地交易 + 失敗時反序補償**,用最終一致換可用性:

```text
訂單 → 扣庫存 → 扣款 → 出貨
若扣款失敗 → 補償:退庫存 → 取消訂單(反序)
```

**補償 ≠ rollback**:各步**已經 commit**(中間狀態**確實發生過**),補償是**語意反向的新操作**(如「退款」而非「撤銷扣款」)——不是資料庫層的回滾。

**追問**:**orchestration**(集中協調者)vs **choreography**(事件協同)取捨;**正向與補償都要冪等**;Saga 狀態要持久化(才能在崩潰後續行)。

---

## Q8. 分散式追蹤解決什麼?trace 和 span 是什麼?

**考點**:分散式追蹤([08-distributed-tracing](../chapters/22-distributed-systems/08-distributed-tracing.md))

**答**:一個請求跨多個服務,分散式追蹤把它的**足跡串成 span 樹**,定位跨服務的慢/錯/路徑(單一服務的 log 看不到全貌)。

- **trace**:一整個請求的完整足跡(一個 **trace id** 貫穿)。
- **span**:一個操作/階段(有起訖時間、parent 關係)。
- **span 樹**:span 的父子結構,反映呼叫鏈。

**跨服務傳播**:靠 **HTTP header(`traceparent`)** 把 context 傳到下游,下游延續同一 trace id。

**定位瓶頸**:看**關鍵路徑上最耗時的 span**。

**追問**:**OpenTelemetry** 是標準(自動埋點、`traceparent` 傳播);生產要**採樣**(機率/尾部,不然量太大);trace id 串起 logs 的價值(見 [Part 19 可觀測性](part19-cloud-native.md#q8-可觀測性三大支柱四個黃金訊號))。

---

⬅️ [Part 21](part21-microservices.md) ｜ [索引](README.md) ｜ ➡️ [Part 23 分析用 SQL 與資料整理](part23-data-analysis.md)
