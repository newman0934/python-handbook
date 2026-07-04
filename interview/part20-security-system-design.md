# Part 20 面試題:安全與系統設計

> 對應 [Part 20 安全與系統設計](../chapters/20-security-system-design/README.md)。**面試密度最高的一 Part**——SQL 注入、密碼雜湊、JWT、XSS/CSRF、系統設計(短網址/限流/分散式 ID)、行為面試。

---

## Q1. 輸入驗證的第一原則?allowlist 和 denylist 差在哪?

**考點**:輸入驗證([01-input-validation](../chapters/20-security-system-design/01-input-validation.md))

**答**:第一原則:**絕不信任外部輸入**(多數漏洞源於信任輸入)。

- **allowlist(正面表列)**:只允許明確合法的(如 `[A-Za-z0-9]`),**fail closed**(不確定就拒絕)——**更安全**。
- **denylist(黑名單)**:擋掉已知壞的——**脆弱**(擋不完,新攻擊繞過)。

**追問**:**驗證(判斷合法、拒絕)vs 淨化/逃逸(轉成安全形式)**——「驗證在輸入、逃逸在輸出且情境相依」;驗證型別/範圍/格式/長度/業務規則;**前端驗證不可信,後端必須驗證**。

---

## Q2.(必考)SQL injection 原理?為什麼參數化查詢徹底有效?

**考點**:注入([02-injection](../chapters/20-security-system-design/02-injection.md))

**答**:SQL injection 的根因是**「資料與程式碼界線被混淆」**——使用者輸入被當 **SQL 程式碼**執行。

**參數化查詢為何徹底有效**:prepared statement **先解析查詢結構、再填值**——參數**永遠是資料**,無法污染已定型的查詢結構(即使輸入含 `'; DROP TABLE`,也只是一個字串值):

```python
cursor.execute("SELECT * FROM users WHERE name = %s", (user_input,))   # 參數化
cursor.execute("SELECT * FROM users WHERE name = '%s'" % user_input)    # 拼接!危險
```

**追問**:**參數化 ≠ 過濾危險字元**(後者是脆弱 denylist,前者是根本解);**識別符(表名/欄名)不能參數化**,要用 allowlist(見 Q1)。

---

## Q3.(必考)密碼要怎麼存?為什麼 SHA-256 不夠?

**考點**:密碼雜湊([08-password-hashing](../chapters/20-security-system-design/08-password-hashing.md))

**答**:**SHA-256 存密碼幾乎和明文一樣糟**——它是**快雜湊 + 沒加鹽**:攻擊者用**彩虹表**(預算好的雜湊對照)+ **GPU 字典攻擊**(每秒億次)輕鬆破解。

正確做法:**慢雜湊 + 加鹽**:

- **鹽(salt)**:每個密碼配一個**唯一**隨機值(不需保密)——破壞彩虹表(每個都要單獨算)與批次破解。
- **慢雜湊**:可調成本、抗暴力(讓每次嘗試都很慢)。

現代選擇排序:**argon2id(首選,吃記憶體抗 GPU)> scrypt > bcrypt > PBKDF2**。

**追問**:密碼是**雜湊**不是加密(單向、不需還原);驗證用**定時比較**(防時序攻擊);雜湊字串**自描述**(含參數,可平滑升級成本)。

---

## Q4. 認證和授權差在哪?什麼是 IDOR / broken access control?

**考點**:認證授權([03-authn-authz](../chapters/20-security-system-design/03-authn-authz.md))

**答**:**認證(authN)= 你是誰**(先);**授權(authZ)= 你能做什麼**(後)。

**IDOR(Insecure Direct Object Reference)/ broken access control** 是 **OWASP 頭號問題**:使用者改 URL 的 id(`/orders/123` → `/orders/124`)就存取到**別人的資源**——因為只認證了「你是登入使用者」,卻沒檢查「這個資源是不是你的」。

**防法:資源層級授權**——每次存取都檢查**擁有權**(不只角色):

```python
order = get_order(id)
if order.user_id != current_user.id:   # 檢查擁有權!
    raise HTTPException(403)
```

**追問**:session vs token 撤銷取捨;**RBAC**(角色—權限—使用者)+ 最小權限;**授權必須在伺服器端、每次存取、涵蓋功能與資源兩層**,別信客戶端。

---

## Q5. JWT 的結構?為什麼說「Base64 不是加密」?

**考點**:JWT([04-jwt](../chapters/20-security-system-design/04-jwt.md))

**答**:JWT 三段 `header.payload.signature`:

- **header**:演算法。
- **payload**:資料(claims,如 user_id)。
- **signature**:用密鑰對前兩段的 **HMAC 簽章**。

**「Base64 不是加密」**:payload 只是 **Base64 編碼**(任何人可解碼讀取)!**簽章保的是「完整性」不是「機密性」**——所以**別在 payload 放敏感資料**(密碼、密鑰)。簽章讓伺服器**無需查庫就能信任**(竄改 payload 會使簽章不符,必被偵測)。

**追問**:JWT(無狀態易擴展、難即時撤銷)vs session;**refresh token** 策略;**`alg: none` / 演算法混淆攻擊**——防禦是**明確指定允許的 algorithms**(別信 token 自報的 alg)。

---

## Q6. XSS、CSRF、SSRF 各是什麼?怎麼防?

**考點**:OWASP([07-owasp-xss-csrf](../chapters/20-security-system-design/07-owasp-xss-csrf.md))

**答**:

| 攻擊 | 機制 | 防禦 |
|------|------|------|
| **XSS** | 注入腳本到頁面(在受害者瀏覽器執行) | **輸出逃逸(情境相依)+ CSP + HttpOnly cookie** |
| **CSRF** | 盜用已登入身分發請求(利用瀏覽器自動帶 cookie) | **CSRF token + SameSite cookie** |
| **SSRF** | 讓**伺服器**替攻擊者發請求 | **allowlist + 封鎖內網 + 禁重導** |

- **XSS**:區分 stored/reflected/DOM;防禦核心是**輸出時逃逸**(把 `<script>` 變文字)。
- **CSRF**:攻擊者**讀不到** CSRF token(同源政策),所以有效;用 token 認證天然免疫。
- **SSRF**:危害是偷雲憑證(`169.254.169.254`)、打內網;**denylist 不夠**(繞法多),要 allowlist。

**追問**:cookie 三屬性——`HttpOnly`(防 XSS 偷)、`Secure`(HTTPS)、`SameSite`(防 CSRF)。

---

## Q7. 密鑰外洩最常見的原因?怎麼管理密鑰?

**考點**:密鑰管理([05-secrets-management](../chapters/20-security-system-design/05-secrets-management.md))

**答**:頭號原因:**寫死在程式 + commit 進 Git**。**後果**:即使刪掉那行,密鑰**仍在 Git 歷史裡**——必須**輪替**(換掉)。

安全梯度:**寫死 < 設定檔 < 環境變數 < Secrets Manager**。Secrets Manager 提供加密儲存、存取控制、動態密鑰、輪替、稽核。

**追問**:用 `SecretStr` 包裝防 print/log 意外洩漏;輪替(定期 + 外洩時立即);最小權限;CI 掃描(detect-secrets)。

---

## Q8. 供應鏈攻擊有哪些?鎖檔 + 雜湊怎麼防?

**考點**:供應鏈([06-supply-chain](../chapters/20-security-system-design/06-supply-chain.md))

**答**:類型:**typosquatting**(仿冒套件名 `reqeusts`)、依賴劫持、**dependency confusion**(私有套件名被公開 registry 搶註)、傳遞依賴漏洞——它們**繞過你自身程式碼的安全**。

**鎖檔 + 雜湊驗證**:lock 檔記錄每個套件的**內容雜湊**(指紋),安裝時驗證——**掉包必被偵測**(雜湊對不上)。**只釘直接依賴不夠,要鎖整棵樹**(傳遞依賴也可能被攻擊)。

**追問**:dependency confusion 防禦(私有 index 優先);漏洞掃描(pip-audit/Dependabot);SBOM、最小化依賴。

---

## Q9.(必考)`pickle.loads` 不可信資料為什麼是 RCE?

**考點**:反序列化([09-deserialization-security](../chapters/20-security-system-design/09-deserialization-security.md))

**答**:pickle 還原「物件」時會**執行程式碼**——`__reduce__` 可指定「還原時呼叫任意函式」,攻擊者構造惡意 pickle 就能執行 `os.system(...)`。**資料變成了指令**,所以 `pickle.loads(不可信資料)` = **RCE(遠端程式碼執行)**。

**JSON 為何安全**:JSON 是**資料格式**(只能表達字串/數字/list/dict),**沒有執行程式碼的表達能力**。

**判準**:**資料有任何可能被攻擊者影響,就別 pickle**。安全替代:JSON、`yaml.safe_load`、MessagePack。

**追問**:常見中招點——Redis 快取、Celery、session、上傳檔(都可能被塞惡意 pickle)。

---

## Q10.(系統設計)設計一個短網址服務。

**考點**:URL shortener([10-system-design-url-shortener](../chapters/20-security-system-design/10-system-design-url-shortener.md))

**答**:走**系統設計框架**(別急著畫架構):**釐清需求 → 估算規模 → API/資料模型 → 核心難點 → 擴展**。

- **容量估算**:短碼長度——`62^7 ≈ 3.5 兆`,**7 碼**夠用。
- **短碼生成**:**base62(自增 id 編碼)**——把資料庫自增 id 用 62 進制(a-z A-Z 0-9)編碼,**無碰撞、可逆、緊湊**(勝過隨機/雜湊要處理碰撞)。
- **高讀寫比 → 快取是關鍵**:短碼查原網址是熱路徑,用 Redis 快取;讀寫分離、分片、CDN。

**追問**:短碼可枚舉的**隱私問題**(自增 id 能猜到別人的)→ 用擾動/加密。

---

## Q11.(系統設計)設計一個限流器。token bucket 怎麼運作?

**考點**:rate limiter([11-system-design-rate-limiter](../chapters/20-security-system-design/11-system-design-rate-limiter.md))

**答**:主流演算法:fixed/sliding window、**token bucket**、leaky bucket。

**token bucket**:桶有 **capacity(突發量)**,以 **refill_rate(平均速率)** 補充權杖,每次請求耗一個,桶空就擋。**惰性補充**(用到才算經過多久補多少)達成 O(1):

```python
tokens = min(capacity, tokens + (now - last) * refill_rate)
if tokens >= 1: tokens -= 1; allow()
else: reject()   # 429
```

- **token bucket**:**允許突發**(桶滿時可連續放行 capacity 個)。
- **leaky bucket**:**強制平滑**(固定速率流出)。

**追問**:**分散式限流**——集中狀態(Redis)+ **原子操作/Lua** 防 race;超限回 **429 + Retry-After + X-RateLimit** header;限流維度(IP/user/API key)。

---

## Q12.(系統設計)分散式系統怎麼生成唯一 ID?Snowflake 的結構?

**考點**:distributed ID([13-system-design-distributed-id](../chapters/20-security-system-design/13-system-design-distributed-id.md))

**答**:**Snowflake** 的 **64-bit 佈局**:

```text
[符號 1] [時間戳 41] [機器 ID 10] [序號 12]
```

- **時間戳(高位)**→ **有序**(按時間遞增,對資料庫索引友善)。
- **機器 ID + 序號** → **唯一**(不同機器不衝突、同毫秒內序號遞增)。
- **本機生成無需協調** → **高效**。

**vs 替代**:UUID(唯一但**無序**、長、傷索引);資料庫自增(有序但**需協調**、單點瓶頸)。Snowflake 兼顧唯一 + 有序 + 高效。

**追問**:**時鐘回撥是頭號陷阱**(NTP 校時倒退導致 ID 重複)——偵測 + 等待/拒絕/告警;機器 ID 要唯一分配。

---

## Q13.(行為面試)怎麼回答行為問題?

**考點**:行為面試([14-behavioral-interview](../chapters/20-security-system-design/14-behavioral-interview.md))

**答**:用 **STAR 框架**:

- **S**ituation(情境):背景。
- **T**ask(任務):你的職責。
- **A**ction(行動):**你**具體做了什麼(重點,用「我」)。
- **R**esult(結果):**量化**成果(數字)。

行為面試的邏輯:**過去行為預測未來**,面試官要**具體真實的故事**而非空泛評價。

**追問**:備 **5-8 個故事庫**(涵蓋衝突、失敗、挑戰、領導、協作,一事多用);**負面問題**(講失敗)——**誠實、擔責、聚焦成長**,別裝完美或甩鍋;用細節與數字,保持誠實(經得起追問)。

---

## Q14. 面試前怎麼準備?回答的結構?

**考點**:面試總覽([15-python-interview-questions](../chapters/20-security-system-design/15-python-interview-questions.md))

**答**:**回答結構**:**定義 → 原理 → 取捨/舉例 → 陷阱/最佳實踐**。面試在意你**懂多深**(深度優先)。

**高頻必考**:GIL/並發選型、引用計數與 GC、可變性、MRO、裝飾器、生成器、N+1、SQL injection、密碼雜湊——幾乎必問(對應本題庫各 Part)。

**系統設計**:熟練短網址(base62)、限流器(token bucket)、分散式 ID(Snowflake)的核心演算法與取捨。

**追問**:每個主題能流暢講「**是什麼 + 為什麼 + 底層 + 取捨**」才算過關。

---

⬅️ [Part 19](part19-cloud-native.md) ｜ [索引](README.md) ｜ ➡️ [Part 21 微服務](part21-microservices.md)
