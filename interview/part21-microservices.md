# Part 21 面試題:微服務

> 對應 [Part 21 微服務](../chapters/21-microservices/README.md)。核心:單體 vs 微服務取捨、gRPC、同步/非同步通訊、服務發現、API gateway、熔斷器。

---

## Q1. 微服務和單體怎麼取捨?為什麼建議「Monolith First」?

**考點**:微服務概論([01-microservices-intro](../chapters/21-microservices/01-microservices-intro.md))

**答**:微服務**用分散式複雜度換團隊自治/獨立部署擴展**——**不是先進與否**的問題。**Monolith First**:多數專案該**從單體開始**,等領域邊界清晰後再拆(一開始就拆,邊界會拆錯、代價巨大)。

**拆分原則**:按**業務能力**(非技術層)、**database per service**、DDD bounded context、適中大小。

**database-per-service** 是核心(各服務獨立演進 schema),但帶來**最終一致性**代價(跨服務沒有單一 ACID 交易,見 [Saga](part22-distributed-systems.md#q7-saga-是什麼補償和-rollback-差在哪))。

**追問**:微服務的**隱藏成本**——網路不可靠、資料一致性、除錯、運維,需要一整套基礎設施。別為了「微服務」而微服務。

---

## Q2. gRPC + protobuf 相對 REST/JSON 有什麼優勢?

**考點**:gRPC([02-grpc-protobuf](../chapters/21-microservices/02-grpc-protobuf.md))

**答**:**二進位緊湊、快、強型別契約、HTTP/2 多工串流**。

**protobuf 為何比 JSON 小**:用**欄位編號**取代欄位名(JSON 每筆都重複欄位名字串)、**varint** 變長編碼、無多餘符號(逗號/引號/括號)。

**追問**:

- **欄位編號的意義?** → 是**契約、不能改**;演進靠**加新編號**(向前/向後相容,舊版忽略不認得的新欄)。
- **四種呼叫模式?** → unary(一對一)、server streaming、client streaming、雙向串流(HTTP/2 支援)。
- **選型?** → **對外 REST**(通用、瀏覽器友善)、**服務間 gRPC**(高效、強型別)。

---

## Q3. 服務間同步和非同步通訊怎麼選?什麼是級聯失敗?

**考點**:服務通訊([03-service-communication](../chapters/21-microservices/03-service-communication.md))

**答**:

- **同步**(REST/gRPC):即時回應,但**時間耦合**(對方必須在線)。
- **非同步**(訊息佇列):**解耦**(故障隔離、削峰、一對多),但**最終一致 + 需冪等**。

**級聯失敗**:同步呼叫鏈 A→B→C,C 慢 → B 卡住等 → A 也卡 → **雪崩**。防護:**逾時 + 熔斷 + 重試**(見 Q7)。

**選型**:**對外 REST、服務間 gRPC、解耦事件用訊息佇列;核心同步、周邊非同步**。

**追問**:非同步的複雜度——訊息重複(需**冪等**)、順序、失敗(死信佇列)、除錯(需分散式追蹤)。

---

## Q4. 服務發現解決什麼?客戶端發現和伺服器端發現差在哪?

**考點**:服務發現([04-service-discovery](../chapters/21-microservices/04-service-discovery.md))

**答**:動態環境中實例 **IP 不斷變**(擴縮、重啟、遷移),服務發現用**邏輯名**找到**當前健康的實例**。

- **客戶端發現**:呼叫方查註冊中心、自己選實例。
- **伺服器端發現**:經負載平衡器/gateway 選(**K8s Service 屬此**)。

機制:**註冊中心 + 健康檢查 + TTL/心跳** 維持「健康實例清單」(暴斃的實例靠 TTL 剔除)。

**追問**:健康過濾與 TTL 剔除的必要(避免把流量送給死掉的實例);常見註冊中心(Consul/etcd/ZooKeeper),K8s 內建發現。

---

## Q5. API gateway 的角色?該做什麼、不該做什麼?

**考點**:API gateway([05-api-gateway](../chapters/21-microservices/05-api-gateway.md))

**答**:**單一入口**——路由、集中橫切關注、聚合、隱藏內部結構。處理的橫切關注:**認證、限流、日誌、CORS、TLS 終結**。

**價值**:**提早拒絕保護後端**(未認證/超限的請求在 gateway 就擋掉,不打到服務),是第一道防線。

**該做 vs 不該做**:該做**路由 + 橫切關注**;**不該放業務邏輯**(否則 gateway 膨脹成新單體)。

**追問**:**BFF(Backend for Frontend)** 模式(為不同前端各一個 gateway);gateway 結合服務發現/負載平衡。

---

## Q6. 三種健康探針差在哪?為什麼「liveness 淺、readiness 深」?

**考點**:健康檢查([06-health-checks](../chapters/21-microservices/06-health-checks.md))

**答**:

- **liveness**:失敗 → **重啟**(應用死了/卡死)。
- **readiness**:失敗 → **移出流量**(暫時不能服務)。
- **startup**:暫緩 liveness(給慢啟動的應用暖機時間)。

**「liveness 淺、readiness 深」**:liveness 只檢查**應用本身活著**(別綁外部依賴);**外部依賴(DB)放 readiness**——因為若 DB 抖動導致 liveness 失敗,會觸發**重啟風暴**(重啟解決不了 DB 掛,反而更糟)。

**追問**:readiness 只綁**關鍵**依賴(非關鍵依賴用降級);`failureThreshold` 過濾抖動;健康端點要**輕量**(別做重查詢)。

---

## Q7.(必考)熔斷器是什麼?三個狀態?和限流差在哪?

**考點**:熔斷器([07-rate-limit-circuit-breaker](../chapters/21-microservices/07-rate-limit-circuit-breaker.md))

**答**:熔斷器用「**快速失敗**」隔離故障、防止雪崩——下游持續失敗時,**直接拒絕**(不再打下游),給它恢復時間。三態狀態機:

```text
CLOSED(正常放行)──連續失敗達閾值──> OPEN(快速失敗,不打下游)
     ↑                                    │ 冷卻時間到
     └──試探成功──── HALF-OPEN(放幾個試探)─┘
                          │ 試探失敗
                          └──> OPEN
```

**half-open** 的作用:冷卻後放幾個請求**試探**下游是否恢復(成功則回 CLOSED、失敗則回 OPEN)。

**限流 vs 熔斷**:

- **限流**:保護**下游**(控制打過去的速率)。
- **熔斷**:保護**自己**(下游故障時快速失敗,不被拖垮)。

**追問**:完整韌性組合——**逾時 + 重試(退避 + 冪等)+ 熔斷 + 艙壁(bulkhead)+ 降級**。熔斷需逾時配合、重試需退避與冪等(否則加劇雪崩)。

---

## Q8. feature flag 怎麼降低發布風險?

**考點**:服務治理([08-service-governance](../chapters/21-microservices/08-service-governance.md))

**答**:**feature flag 解耦「部署」與「發布」**——程式部署了但功能可**用開關控制**:金絲雀(先開給 1%)、A/B 測試、**kill switch**(出事立刻關,不用回滾部署)。

**分散式設定管理**:集中、一致、**動態更新(watch,不重啟)**、版本稽核——勝過環境變數(改了要重啟)。

**追問**:feature flag 評估要**確定性**(同使用者一致,見 [Part 30 A/B](part30-production-ai.md));百分比發布邏輯;服務治理範疇——設定、發現、限流熔斷、可觀測性、服務網格。

---

⬅️ [Part 20](part20-security-system-design.md) ｜ [索引](README.md) ｜ ➡️ [Part 22 分散式系統](part22-distributed-systems.md)
