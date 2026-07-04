# Part 16 面試題:架構與設計

> 對應 [Part 16 架構](../chapters/16-architecture/README.md)。資深職位核心——分層、Clean Architecture、DI、SOLID、DDD、設計模式。面試重點是**能講清楚「解決什麼問題」與「何時是過度工程」**。

---

## Q1. 分層架構是什麼?為什麼要分層?

**考點**:分層架構([01-layered-architecture](../chapters/16-architecture/01-layered-architecture.md))

**答**:三層 + **單向依賴**(下層不知道上層):

- **表現層(presentation)**:HTTP、路由、序列化。
- **業務層(business/service)**:業務規則、領域邏輯。
- **資料層(data)**:資料庫存取。

核心好處:**關注點分離 + 可測試性**——業務層**純淨**(不碰 HTTP/DB),能獨立測試(最大回報)。對比「大泥球」(全糾纏、難測、難改、難換)。

**追問**:業務層拋**領域例外**(非 HTTPException),表現層映射成 HTTP(見 [Part 14 Q12](part14-web.md#q12端點怎麼回錯誤為什麼領域例外要在-web-層才映射成-http));DI 讓層可替換可測試;分層是 Clean Architecture、DDD 的基礎。

---

## Q2. Clean Architecture 的核心是什麼?和分層架構差在哪?

**考點**:Clean Architecture([02-clean-architecture](../chapters/16-architecture/02-clean-architecture.md))

**答**:核心是**依賴規則**——**依賴只指向內層**,核心業務規則**不依賴框架/DB/UI**(它們是可替換的「細節」)。靠**依賴反轉**達成:**內層定義介面(port)、外層實作**,依賴方向反轉成指向核心。

**vs 分層架構**:分層的業務層**依賴具體**資料層;Clean 讓業務**只依賴抽象**——換 DB/框架不動核心。同心圓四層:Entities / Use Cases / Interface Adapters / Frameworks & Drivers。

**追問**:**務實觀點**(面試加分)——它有成本(更多間接層),**簡單專案別過度套用**;Hexagonal/Onion/DDD 是同一思想的變體。

---

## Q3. 什麼是依賴注入(DI)?Python 需要 DI 容器嗎?

**考點**:DI([03-dependency-injection](../chapters/16-architecture/03-dependency-injection.md))

**答**:DI 是**控制反轉**的一種——不自己建立依賴,由**外部注入**(把「建立」與「使用」分開):

```python
class OrderService:
    def __init__(self, repo: OrderRepo):   # 注入,而非 self.repo = SQLOrderRepo()
        self.repo = repo
```

回報:**鬆耦合、可測試(注入 mock)、可替換、依賴明確**。**建構子注入**最常用,且應**依賴抽象(Protocol/ABC)而非具體**。

**追問**:

- **Python 需要 DI 容器嗎?** → **通常不需要**(動態語言,手動注入夠清楚);用 `Protocol` 定義依賴介面。
- **框架的 DI?** → FastAPI 的 `Depends`、pytest 的 fixture 都是 DI。**composition root**(最外層組裝依賴圖)。

---

## Q4. Repository 模式是什麼?什麼時候該用?

**考點**:Repository([04-repository-pattern](../chapters/16-architecture/04-repository-pattern.md))

**答**:把資料存取封裝成「**像記憶體集合**」的介面,業務層**不知道背後是 SQL/NoSQL/記憶體**(持久化無知):

```python
class OrderRepo(Protocol):
    def get(self, id: int) -> Order: ...
    def save(self, order: Order) -> None: ...
# 業務層只依賴這個介面;測試用記憶體實作、生產用 SQL 實作
```

價值:業務層與資料存取**解耦**、查詢集中、換 DB 不動業務、**測試用記憶體實作不碰 DB**。

**追問**:介面由**業務層擁有**、實作在外層(依賴反轉);**Unit of Work** 管跨 repository 的交易邊界(SQLAlchemy Session 就是 UoW + identity map);**務實**:ORM 某程度已是 repository,簡單 CRUD 未必需要額外一層。

---

## Q5.(必考)SOLID 五原則各解決什麼問題?

**考點**:SOLID([05-solid](../chapters/16-architecture/05-solid.md))

**答**:重點是**說出每條解決的問題**(不是死背字母):

| 原則 | 解決的問題 |
|------|-----------|
| **S**RP 單一職責 | 一個類別職責混雜、改一處動全身 |
| **O**CP 開放封閉 | 加功能要改既有程式(該用多型擴充,如 if/elif → 策略) |
| **L**SP 里氏替換 | 子類別破壞父類別契約(企鵝是鳥但不會飛) |
| **I**SP 介面隔離 | 胖介面逼實作用不到的方法 |
| **D**IP 依賴反轉 | 高層綁死低層具體(該依賴抽象,`new` 具體 → 注入) |

**追問**:**DIP 就是 DI 的理論基礎**;Repository/Clean Architecture 都是 SOLID 的實踐;Python 落地用 Protocol、組合、函式分派(不必事事 ABC)。**務實**:SOLID 是指導原則不是教條,過度套用 = 過度工程。

---

## Q6. 設計模式在 Python 裡有什麼不同?Singleton 為什麼常是反模式?

**考點**:設計模式([06-design-patterns](../chapters/16-architecture/06-design-patterns.md))

**答**:三大類:創建型(Factory)、結構型(Adapter)、行為型(Strategy)。常用模式:Strategy(執行時切換演算法)、Factory(集中建立)、Observer(一對多通知)、Adapter(不相容介面協作)。

**Python 讓許多模式變輕/內建**:

- **函式即 Strategy**(傳函式當參數)。
- **字典即 Factory**(dispatch table)。
- **模組/`lru_cache` 即 Singleton**。
- **`@decorator`** 是語言級的裝飾器模式。

**Singleton 常是反模式**:全域狀態、難測(測試間互相污染)、隱藏依賴——**多用 DI 取代**。

**追問**:**面試加分**:模式是**工具不是目標**,強調 YAGNI、別過度工程,能說出「何時該用、何時是過度設計」。

---

## Q7. DDD 是什麼?Entity 和 Value Object 差在哪?

**考點**:DDD([08-ddd](../chapters/16-architecture/08-ddd.md))

**答**:DDD(領域驅動設計)是「**把業務領域放設計中心**」的方法論。核心價值:**統一語言**(程式術語 = 業務術語)、**bounded context**(劃分子領域邊界)。

- **Entity**:**有身分**——身分定義相等(兩個 Order 即使欄位全同,id 不同就是不同)。例:Order、User。
- **Value Object**:**無身分**——由**值**定義相等、**不可變**。例:Money、Address(兩個 100 元就是相等)。

**Aggregate**:一致性邊界——透過 **root** 操作、root 維護不變條件、repository 以 aggregate 為單位、**一交易一 aggregate**。

**追問**:充血 vs 貧血模型(DDD 主張**業務規則放進領域物件**);**務實**:DDD 為**複雜領域**設計,簡單 CRUD 是過度工程;bounded context 是**微服務拆分的理論依據**。

---

## Q8. Hexagonal(Ports & Adapters)架構?

**考點**:Hexagonal([09-hexagonal](../chapters/16-architecture/09-hexagonal.md))

**答**:核心透過 **ports(介面)** 與外界互動,**adapters** 實作 ports 連接真實技術,核心**不依賴具體技術**。兩種 port:

- **driving/primary port**:外界**驅動核心**(Web/CLI/測試)。
- **driven/secondary port**:核心**驅動外界**(DB/email),**由核心定義**(依賴反轉)。

好處:**可插拔 + 可測試**——一核心多進入點、一 port 多實作、測試全插假 adapter。

**追問**:Hexagonal/Clean/Onion/分層是**同一思想**(依賴指向核心)的不同表述,Hexagonal 的貢獻是 ports/adapters 詞彙與**兩側對稱**視角;常與 DDD 搭配。

---

## Q9. 事件驅動架構的價值?工作佇列和 pub/sub 差在哪?

**考點**:事件驅動([10-event-driven-mq](../chapters/16-architecture/10-event-driven-mq.md))

**答**:用**事件**解耦「發生的事」與「反應」——主流程快、鬆耦合、可靠(可重試)、可擴展;代價是**最終一致**與複雜度。

- **工作佇列(point-to-point)**:一任務**一個 worker** 處理(分工)。工具:Celery/RabbitMQ。
- **pub/sub**:一事件**多個訂閱者**都收到(廣播)。工具:Kafka。

**追問**:**「至少一次投遞 → 消費者要冪等」** 是關鍵(重試、死信佇列、順序不保證);Celery(Python 背景任務)/RabbitMQ(可靠佇列)/Kafka(高吞吐事件流)的定位;**務實**:核心即時一致操作同步、周邊非同步,別過度事件化。

---

## Q10. 設定該怎麼管理?為什麼用環境變數?

**考點**:設定管理([11-config-management](../chapters/16-architecture/11-config-management.md))

**答**:原則:**設定與程式分離**——凡**隨部署環境改變**的值就是設定(檢驗法:「**能否開源而不洩漏機密**」)。對應 12-factor 的「store config in the environment」。

**為何用環境變數而非設定檔**:語言/OS 中立、不易誤入版控、部署平台原生支援、**同一 build 跑遍所有環境**。

**pydantic-settings** 的價值:型別註解 → **自動轉型 + 驗證 + fail fast**(勝過手寫 `os.getenv`):

```python
class Settings(BaseSettings):
    database_url: str
    debug: bool = False       # 自動轉型 + 驗證
```

**追問**:**字串轉 bool 陷阱**(`bool("false") == True`,環境變數皆字串);機密管理(`.env` 進 `.gitignore`、正式用 secrets manager、`SecretStr` 避免洩漏、外洩要輪替);設定優先順序(預設 < .env < 環境變數 < 直接傳入)、集中定義啟動建立一次注入使用。

---

⬅️ [Part 15](part15-database.md) ｜ [索引](README.md) ｜ ➡️ [Part 17 資料處理與科學計算](part17-data-science.md)
