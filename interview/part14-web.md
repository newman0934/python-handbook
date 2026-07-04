# Part 14 面試題:Web 開發

> 對應 [Part 14 Web](../chapters/14-web/README.md)。**後端職位核心**——WSGI/ASGI、REST、認證授權、pydantic、async 陷阱、CORS/CSRF 安全都是高頻題。

---

## Q1. WSGI 和 ASGI 差在哪?

**考點**:WSGI/ASGI([01-wsgi-asgi](../chapters/14-web/01-wsgi-asgi.md))

**答**:兩者都是「**應用伺服器 ↔ Python 應用**」的標準介面(讓框架與伺服器解耦)。

| | WSGI | ASGI |
|---|------|------|
| 模型 | **同步** | **非同步**(async/await) |
| 並發 | 一請求一 worker | 單 worker 高並發 |
| 框架 | Flask/Django | FastAPI |
| 伺服器 | gunicorn | uvicorn |
| WebSocket | ✗ | ✓ |

ASGI 的優勢源自 **asyncio**——I/O 密集高並發、WebSocket/長連線,這是 FastAPI 用 ASGI 的原因。

**追問**:請求鏈:**瀏覽器 → nginx → gunicorn/uvicorn → WSGI/ASGI → 應用**。**生產別用開發伺服器**(`app.run()`/`--reload`);FastAPI 生產常用 **gunicorn + uvicorn workers**(多核 + async)。

---

## Q2. HTTP 方法的語意?401 和 403、400 和 422 差在哪?

**考點**:HTTP 基礎([02-http-basics](../chapters/14-web/02-http-basics.md))

**答**:HTTP 是**無狀態**的請求-回應協定。方法語意:

| 方法 | 語意 | 安全 | 冪等 |
|------|------|------|------|
| GET | 讀 | ✓ | ✓ |
| POST | 建 | ✗ | ✗ |
| PUT | 完整更新 | ✗ | ✓ |
| PATCH | 部分更新 | ✗ | ✗ |
| DELETE | 刪 | ✗ | ✓ |

- **安全**:不改變狀態(GET)。**冪等**:做一次和做多次結果相同(PUT/DELETE)。

狀態碼易混淆的:

- **401 vs 403**:401 = **未認證**(不知道你是誰,該登入);403 = **已認證但無權限**(知道你是誰但你不能做這事)。
- **400 vs 422**:400 = 請求格式壞;422 = 格式對但**驗證失敗**(值不合法)。

**追問**:無狀態 → 狀態靠 cookie/token 維持 → 利於水平擴展。這是 REST 的基礎。

---

## Q3. FastAPI 為什麼強?它用型別註記做了什麼?

**考點**:FastAPI([04-fastapi-basics](../chapters/14-web/04-fastapi-basics.md))

**答**:FastAPI **用型別註記驅動一切**——一份型別多用途:

- **自動驗證輸入**(pydantic):型別不符自動回 **422 + 詳細訊息**。
- **自動產生 OpenAPI 文件**(Swagger `/docs`)——殺手功能。
- **原生 async**(ASGI):高並發。

```python
@app.post("/users")
def create(user: UserIn) -> UserOut:   # UserIn 自動驗證、UserOut 過濾回應
    ...
```

**追問**:

- **`response_model`/回傳型別的重要?** → **過濾回應欄位**,別洩漏敏感資料(如密碼雜湊)。
- **async def vs def?** → async def 高並發;`def` 端點 FastAPI **自動丟執行緒池**(見 Q10)。
- **參數判定?** → 路徑 `{}` → 路徑參數;pydantic 模型 → body;其餘簡單型別 → query。**具體路徑要放參數路徑之前**(`/users/me` 在 `/users/{id}` 前,常見陷阱)。

---

## Q4. pydantic 和 mypy 是什麼關係?

**考點**:pydantic([06-pydantic-validation](../chapters/14-web/06-pydantic-validation.md))

**答**:兩者互補、管不同的事:

- **mypy**:**靜態**檢查——檢查你**程式碼**的型別(執行前)。
- **pydantic**:**執行期**驗證——驗證**外部進來的資料**(請求 body、設定檔),不合法拋 `ValidationError`。

外部資料(使用者輸入)靜態檢查管不到,要靠 pydantic 在執行期把關。pydantic 是 FastAPI 的驗證引擎:

```python
class User(BaseModel):
    name: str
    age: int = Field(gt=0)        # 約束
    @field_validator("name")
    def not_empty(cls, v): ...
```

**追問**:

- **pydantic v2?** → `model_dump`/`model_validate`(取代 v1 的 `dict`/`parse_obj`),Rust 核心快。
- **實務?** → `model_dump(exclude=...)` 過濾敏感欄位;**請求模型和回應模型分開**(避免洩漏/耦合)。

---

## Q5. REST API 怎麼設計?有哪些反模式?

**考點**:REST([08-rest-api](../chapters/14-web/08-rest-api.md))

**答**:REST 原則:**資源用名詞(複數)、動作用 HTTP 方法、配對狀態碼**:

```text
GET    /users          列出(200)         ← 不是 /getUsers
POST   /users          建立(201)
GET    /users/{id}     取得(200/404)
PUT    /users/{id}     更新(200)
DELETE /users/{id}     刪除(204)
```

**反模式**:動詞放 URL(`/getUser`、`/deleteUser`)、什麼都回 200(該用 4xx/5xx)、大集合不分頁。

**追問**:**分頁/篩選/排序用 query 參數**(不放路徑),大集合**一定分頁**;API 版本用 URL 前綴(`/v1/`);一致的命名與錯誤格式。

---

## Q6.(必考)認證和授權差在哪?密碼怎麼存?JWT 和 Session 怎麼選?

**考點**:認證授權([09-auth](../chapters/14-web/09-auth.md))

**答**:

- **認證(authentication, authn)**:「**你是誰**」——驗證身分(登入),失敗回 **401**。
- **授權(authorization, authz)**:「**你能做什麼**」——檢查權限,失敗回 **403**。**先認證再授權**。

**密碼儲存**:**絕不明文!用 bcrypt/argon2 雜湊**(加 salt、單向、驗證時比對雜湊)。**別用 MD5/SHA**(太快,易暴力破解)。

**JWT vs Session**:

| | JWT | Session |
|---|-----|---------|
| 狀態 | **無狀態**(資訊在 token) | 有狀態(伺服器存) |
| 擴展 | 易(不需共享 session store) | 需共享 store |
| 撤銷 | **難**(token 到期前有效) | 易(刪 session) |
| 適合 | API/微服務 | 傳統 Web |

**追問**:FastAPI 用 **`Depends`** 實作(`get_current_user`、`require_role`);**授權要檢查資源擁有權**(不只角色——別讓 A 改 B 的資料);JWT 要**驗證簽章**、SECRET 用環境變數、全程 HTTPS。

---

## Q7. `Depends` 是什麼?為什麼認證用 Depends 而非 middleware?

**考點**:依賴注入([11-fastapi-depends](../chapters/14-web/11-fastapi-depends.md))

**答**:`Depends` 是 FastAPI 的**依賴注入**——共用邏輯(DB session、當前使用者、分頁參數)抽成依賴,端點宣告需要,FastAPI **自動注入**:

```python
def get_db():
    db = SessionLocal()
    try: yield db          # yield 依賴,含清理(類似 fixture)
    finally: db.close()

@app.get("/users")
def list_users(db=Depends(get_db), user=Depends(get_current_user)): ...
```

**為何認證用 Depends 而非 middleware**:

- **可依端點**(某些端點要認證、某些不要),middleware 是全域的。
- **可測試**——`dependency_overrides` 讓測試**覆寫依賴**注入 mock(見 Q14)。
- **可組合**(巢狀依賴:認證依賴用 DB 依賴,自動解析鏈)。

**追問**:middleware(真正跨所有端點的橫切:日誌/CORS/計時)vs Depends(特定端點的依賴:認證/DB)——各有定位。

---

## Q8. middleware 是什麼?洋蔥模型?

**考點**:middleware([07-middleware](../chapters/14-web/07-middleware.md))

**答**:middleware 是「**包在請求-回應外圍的橫切關注**」,用**洋蔥模型**——請求**由外往內**穿過各層、回應**由內往外**穿回,`call_next` 是分界:

```python
@app.middleware("http")
async def timing(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)      # 分界:進入內層
    response.headers["X-Time"] = str(time.perf_counter() - start)
    return response                          # 必須 return response
```

常見用途:日誌、計時、CORS、統一錯誤格式、限流。

**追問**:middleware 要**輕量、async 別阻塞、必須 return response**;順序影響包裹層次;內建的 CORS/GZip 用 `add_middleware`。

---

## Q9.(必考)在 `async def` 端點裡放阻塞操作會怎樣?

**考點**:async web([12-async-web-background](../chapters/14-web/12-async-web-background.md))

**答**:**卡住整個 event loop——所有請求停擺!** async 端點的高並發來自 async I/O,但 `async def` 裡的**同步阻塞**(`time.sleep`、`requests.get`、重 CPU)會霸佔單一 event loop 執行緒(同 [Part 09](part09-concurrency.md#q11必考在-async-函式裡呼叫-timesleep5-或-requestsget-會怎樣))。

解法:

- **一路 async 到底**(用 async 函式庫 httpx/asyncpg)。
- **阻塞/CPU 用 `def` 端點**(FastAPI 自動丟執行緒池)或 `asyncio.to_thread`。

**追問**:`BackgroundTasks`(輕量、回應後執行,如寄信)vs **Celery**(重、可靠、獨立 worker,適合長任務);CPU 密集別用 async web(用行程池)。

---

## Q10.(安全必考)CORS、CSRF、cookie 安全屬性?

**考點**:CORS/cookie([14-cors-cookie-session](../chapters/14-web/14-cors-cookie-session.md))

**答**:

- **同源政策**:瀏覽器安全機制,禁止跨源存取。**CORS** 是「有條件放行跨源」。**別用 `"*"` 配 credentials**(CSRF 風險),要**明確列來源**。
- **CSRF(跨站請求偽造)**:惡意站點利用瀏覽器**自動帶 cookie** 偽造請求。防護:cookie 設 **`samesite`**、CSRF token,或**用 token 認證**(放 Authorization 標頭,不自動帶,天然免疫)。
- **cookie 安全屬性**:**`httponly`**(JS 讀不到,防 XSS 偷)、**`secure`**(只走 HTTPS)、**`samesite`**(防 CSRF)——session cookie 三個都要設。

**追問**:session cookie(自動帶、有 CSRF 風險)vs token 認證(Authorization 標頭、無 CSRF、適合 API);CORS 是**瀏覽器機制**(不擋直接的 curl/後端請求),要用 HTTPS。

---

## Q11. Jinja2 模板有什麼安全重點?

**考點**:模板([10-templates](../chapters/14-web/10-templates.md))

**答**:Jinja2 是 Python 主流模板引擎(`{{ }}` 輸出、`{% %}` 邏輯、模板繼承)。**關鍵安全:Jinja2 預設自動跳脫,防 XSS**——把使用者輸入當**文字**顯示(`<script>` 變成 `&lt;script&gt;`)。**別對不可信資料用 `| safe`**(關掉跳脫 = XSS 漏洞)。

**追問**:靜態檔開發用 StaticFiles、**生產由 nginx 提供**(更快);邏輯留後端、模板只展示;伺服器渲染(模板)vs 純 API + 前端框架的架構取捨。

---

## Q12. 端點怎麼回錯誤?為什麼領域例外要在 Web 層才映射成 HTTP?

**考點**:例外處理([16-exception-handlers](../chapters/14-web/16-exception-handlers.md))

**答**:用 **`HTTPException(status_code, detail)`** 回對的狀態碼(404/403/400),**別讓例外冒成 500**。

**分層**:**領域邏輯拋領域例外(如 `OutOfStockError`),Web 層用例外處理器映射成 HTTP**——好處是領域層**乾淨、可重用、好測**(不依賴 HTTP),對應[分層架構](part16-architecture.md):

```python
@app.exception_handler(OutOfStockError)
def handle(request, exc):
    return JSONResponse(status_code=409, content={"error": str(exc)})
```

**追問**:**錯誤回應絕不洩漏堆疊/內部細節**(資安)——未預期例外回一般 500、細節進 log;統一錯誤格式(code/message);可覆寫 `RequestValidationError`。

---

## Q13. 什麼時候用 WebSocket?水平擴展有什麼問題?

**考點**:WebSocket([13-websocket](../chapters/14-web/13-websocket.md))

**答**:

| | HTTP | WebSocket |
|---|------|-----------|
| 模式 | 請求-回應 | **全雙工雙向** |
| 連線 | 短暫 | **持久** |
| 推送 | 不能 | **伺服器可主動推** |

WebSocket 適合**即時**場景(聊天、通知、串流),**需要 ASGI**(FastAPI 支援,WSGI/Flask 不支援)。

**水平擴展問題**:多個伺服器實例時,連在實例 A 的使用者收不到實例 B 的訊息——**需要 Redis pub/sub 或訊息佇列跨實例廣播**(連結[分散式](part22-distributed-systems.md))。

**追問**:連線生命週期(`accept` → `while receive/send` → `WebSocketDisconnect`);要處理斷線清理、認證 WebSocket;**SSE** 是單向推送的簡單替代。

---

## Q14. 怎麼測 FastAPI?怎麼測認證端點而不用真登入?

**考點**:TestClient([15-testclient](../chapters/14-web/15-testclient.md))

**答**:用 **`TestClient`**(基於 httpx)在**記憶體內**測 API——不啟動伺服器、走**完整流程**(middleware/驗證/路由)、快又完整:

```python
client = TestClient(app)
def test_get_user():
    resp = client.get("/users/1")
    assert resp.status_code == 200
```

**測認證端點**:用 **`dependency_overrides` 換 mock 使用者/DB**——不必真登入、不碰真實資源(這正是 `Depends` 可測試的體現):

```python
app.dependency_overrides[get_current_user] = lambda: fake_user
```

**追問**:測各種情況(成功、422、404、401、403);配 pytest fixture 管理 client 與覆寫;TestClient 也能測 WebSocket;測試進 CI。

---

## Q15. GraphQL 解決什麼?N+1 問題是什麼?REST 還是 GraphQL?

**考點**:GraphQL([17-graphql](../chapters/14-web/17-graphql.md))

**答**:GraphQL 解決 REST 的 **over-fetching**(回太多用不到的欄位)與 **under-fetching**(要多次往返才拿齊),讓**客戶端精確指定資料形狀**。三核心:**schema**(強型別契約)、**query**(客戶端指定欄位/巢狀)、**resolver**(怎麼取值)。

**N+1 問題(頭號陷阱)**:查 N 個作者的書,每個作者各發一次 DB 查詢 → 1 + N 次查詢。解法:**DataLoader** 批次化(把 N 次合併成 1 次)。

**REST vs GraphQL**:GraphQL 靈活但**伺服器複雜、快取難、有查詢複雜度攻擊**;**不是 REST 的全面替代**,依場景並存。

**追問**:Python 用 **Strawberry/Graphene**;三種操作(query/mutation/subscription);schema 自我文件化。

---

## Q16. API 設計怎麼從「能用」提升到「好用可演進」?

**考點**:API 設計([18-api-design](../chapters/14-web/18-api-design.md))

**答**:資深工程師的體現:

- **版本管理**:URL vs header 版本;區分破壞性/非破壞性變更;版本共存 + 淘汰期。
- **分頁**:**offset**(簡單、能跳頁)vs **cursor**(穩定、快,適合深分頁/變動資料)。
- **ETag/條件請求**:內容指紋 + `If-None-Match` → **304 空 body**(省頻寬)。
- **一致性**:統一錯誤格式、查詢參數約定、正確狀態碼、命名慣例。
- **寫入冪等、限流回 429、用 OpenAPI 文件化**。

**追問**:offset 深分頁效能差(要掃過前面所有列),大資料/即時流用 cursor。

---

⬅️ [Part 13](part13-tooling-packaging.md) ｜ [索引](README.md) ｜ ➡️ [Part 15 資料庫](part15-database.md)
