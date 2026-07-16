# 認證與授權

> 「你是誰」和「你能做什麼」是兩件常被混為一談、卻必須分開的事——前者是認證（authentication）、後者是授權（authorization）。這章講清楚兩者的差別、密碼為何不能明文存、以及 JWT 與 session 怎麼選。

## 💡 白話導讀（建議先讀）

進一棟辦公大樓,門禁問你**兩個不同的問題**：

1. **「你是誰?」**——刷卡驗身分 → **認證(Authentication / authn)**:登入、驗帳密、驗 token。
2. **「你能進幾樓?」**——身分確認後查權限 → **授權(Authorization / authz)**:admin 才能刪、只能看自己的資料。

順序永遠是**先認證、再授權**。兩個常考狀態碼正好對應：

- **401 Unauthorized**——「你是誰都不知道」(沒登入/token 無效)。※名字取得爛,它其實是「未認證」
- **403 Forbidden**——「知道你是誰,但你不准」(已登入,權限不夠)

現代 API 的認證主流長這樣(章內逐一實作)：

```text
登入:帳密 → 驗過 → 簽發 token(如 JWT)
之後每個請求:Authorization: Bearer <token> → 後端驗 token → 知道你是誰
```

(為什麼用 token 不用 session?呼應 [HTTP 無狀態](02-http-basics.md)與水平擴展——章內比較。)

密碼儲存的鐵律,[練習題](../../exercises/part20/)做過的:**絕不存明文,存加鹽慢雜湊**(bcrypt/argon2/PBKDF2)——資料庫被拖走也反推不出密碼。

FastAPI 落地:認證邏輯寫成 [Depends](11-fastapi-depends.md)(`get_current_user`),端點宣告即受保護——下下章的依賴注入在這裡大放異彩。

## Why（為什麼）

幾乎每個 Web 應用都要「登入」與「權限控制」——這就是**認證與授權**。做錯會有嚴重安全後果：密碼明文儲存（外洩災難）、token 沒驗證（任何人可假冒）、權限沒檢查（越權存取）。理解「認證 vs 授權」的區別、密碼該怎麼存（雜湊）、token（JWT）與 session 的機制，是保護 Web 應用的核心安全知識。這章講清楚概念與實踐（實作細節見 [JWT](../20-security-system-design/04-jwt.md)、[認證授權](../20-security-system-design/03-authn-authz.md)、[密碼雜湊](../20-security-system-design/08-password-hashing.md)）。

## Theory（理論：認證 vs 授權）

門禁的兩個不同問題——**兩個常被混淆但根本不同的概念**：

- **認證（Authentication，authn）**：「**你是誰**」——確認使用者身分（登入：驗證帳密、驗證 token）——刷卡。
- **授權（Authorization，authz）**：「**你能做什麼**」——確認已認證的使用者有沒有權限做某操作（admin 才能刪除、只能看自己的資料）——查樓層權限。

順序：**先認證（確認身分）→ 再授權（檢查權限）**。

對應狀態碼（見 [HTTP 基礎](02-http-basics.md)）：

- **401 Unauthorized**：未認證（你是誰？沒登入）——名字誤導，實為「未認證」。
- **403 Forbidden**：已認證但未授權（知道你是誰，但你不准）。

## Specification（規範：認證流程）

```python
# --- 密碼雜湊（絕不明文存密碼）---
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"])
hashed = pwd_context.hash("plaintext")           # 註冊時雜湊
pwd_context.verify("plaintext", hashed)          # 登入時驗證

# --- JWT token 認證（FastAPI）---
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_token(user_id: int) -> str:
    return jwt.encode({"sub": str(user_id)}, SECRET_KEY, algorithm="HS256")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="無效的 token")

# 授權：檢查權限
def require_admin(user = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理員權限")
    return user
```

## Implementation（密碼雜湊、token vs session、授權）

### 🔴 密碼絕不明文儲存——用雜湊

**最重要的安全鐵律**：**密碼絕不能明文（或可逆加密）儲存**——資料庫外洩時明文密碼是災難。要用**單向雜湊（hash）** + salt：

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

# 註冊：存雜湊，不存明文
hashed = pwd_context.hash("user_password")   # 存這個到 DB
# DB 只存雜湊值，永遠不存明文

# 登入：驗證（不「解密」——雜湊不可逆）
is_valid = pwd_context.verify("user_password", hashed)   # True/False
```

用 **bcrypt / argon2**（專為密碼設計、慢、有 salt，見 [密碼雜湊](../20-security-system-design/08-password-hashing.md)）——**別用 MD5/SHA（快、易破解）、別自己實作**。雜湊是**單向**的——登入時不「解密」，而是「把輸入的密碼同樣雜湊、比對」。

### Token 認證（JWT）vs Session

兩種維持登入狀態的方式（HTTP 無狀態，見 [HTTP 基礎](02-http-basics.md)）：

**Token 認證（JWT）**——客戶端拿一個 token，每次請求帶上：

```text
登入 → 伺服器發 JWT token → 客戶端存 token
之後每次請求：Authorization: Bearer <token>
伺服器驗證 token（不查 DB）→ 知道是誰
```

**Session 認證**——伺服器存 session、客戶端存 session id（cookie）：

```text
登入 → 伺服器建 session、發 session id（cookie）
之後每次請求：帶 cookie
伺服器查 session store → 知道是誰
```

| | JWT（token） | Session |
|--|-------------|---------|
| 狀態 | 無狀態（token 自帶資訊） | 有狀態（伺服器存 session） |
| 擴展性 | 好（不必共享 session store） | 需共享 session store |
| 撤銷 | 難（token 有效期內都算數） | 易（刪 session） |
| 適合 | API、微服務、跨域 | 傳統 Web、需要即時撤銷 |

**JWT 適合 API/微服務**（無狀態、易擴展）；**session 適合傳統 Web**（易撤銷）。JWT 細節見 [JWT](../20-security-system-design/04-jwt.md)。

### 授權：檢查權限

認證後，**授權檢查「能不能做這個操作」**——常見模式：

```python
# 角色式（RBAC）
def require_role(role: str):
    def checker(user = Depends(get_current_user)):
        if role not in user.roles:
            raise HTTPException(403, "權限不足")
        return user
    return checker

@app.delete("/users/{id}")
def delete_user(id: int, admin = Depends(require_role("admin"))):
    ...   # 只有 admin 能到這

# 資源擁有權
@app.get("/orders/{id}")
def get_order(id: int, user = Depends(get_current_user)):
    order = get_order_from_db(id)
    if order.owner_id != user.id:
        raise HTTPException(403, "不是你的訂單")   # 只能看自己的
    return order
```

授權模式：**角色式（RBAC，admin/user）、資源擁有權（只能存取自己的）、權限式（細粒度）**。FastAPI 常用 `Depends` 實作（見 [Depends](11-fastapi-depends.md)），把認證+授權當依賴注入。

### FastAPI 的認證整合

FastAPI 提供 `OAuth2PasswordBearer` 等安全工具，配 `Depends` 做認證：

```python
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/me")
def read_me(current_user = Depends(get_current_user)):   # 需要認證
    return current_user
```

`Depends(get_current_user)` 讓「需要登入」變成一個依賴——加到端點就要求認證，且自動反映在文件。這是 FastAPI 認證的慣用法。

## Code Example（可執行的 Python 範例）

```python
# auth_demo.py
from __future__ import annotations

import hashlib
import hmac
import secrets


# 註：示範用簡化雜湊；正式環境用 passlib + bcrypt/argon2
def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """雜湊密碼（示範；正式用 bcrypt/argon2）。"""
    if salt is None:
        salt = secrets.token_hex(16)  # 每個密碼獨立的 salt
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return hashed.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """驗證密碼（雜湊後比對，不解密）。"""
    computed, _ = hash_password(password, salt)
    return hmac.compare_digest(computed, stored_hash)  # 防時序攻擊


def check_permission(user_roles: list[str], required: str) -> tuple[int, str]:
    """授權檢查。回傳 (狀態碼, 訊息)。"""
    if required in user_roles:
        return 200, "允許"
    return 403, "權限不足（已認證但未授權）"


def demo() -> None:
    # 1. 密碼雜湊（註冊時）
    stored_hash, salt = hash_password("mySecret123")
    print(f"儲存的雜湊（前16字）: {stored_hash[:16]}...")
    print("→ DB 只存雜湊，永遠不存明文密碼")

    # 2. 驗證（登入時）
    print(f"\n正確密碼驗證: {verify_password('mySecret123', stored_hash, salt)}")
    print(f"錯誤密碼驗證: {verify_password('wrong', stored_hash, salt)}")

    # 3. 授權
    print("\n授權檢查：")
    for role_needed in ["user", "admin"]:
        status, msg = check_permission(["user"], role_needed)
        print(f"  需要 {role_needed}: {status} {msg}")

    print("\n重點：認證(你是誰,401) vs 授權(能做什麼,403)；密碼用雜湊絕不明文")


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python auth_demo.py
儲存的雜湊（前16字）: a1b2c3d4e5f6...
→ DB 只存雜湊，永遠不存明文密碼

正確密碼驗證: True
錯誤密碼驗證: False

授權檢查：
  需要 user: 200 允許
  需要 admin: 403 權限不足（已認證但未授權）

重點：認證(你是誰,401) vs 授權(能做什麼,403)；密碼用雜湊絕不明文
```

## Diagram（圖解：認證 → 授權）

```mermaid
flowchart TD
    A[請求] --> B{已認證?(你是誰)}
    B -- 否 --> C[401 Unauthorized]
    B -- 是 --> D{已授權?(能做這個嗎)}
    D -- 否 --> E[403 Forbidden]
    D -- 是 --> F[執行操作]
    style C fill:#ffebee
    style E fill:#fff3e0
    style F fill:#e8f5e9
```

## Best Practice（最佳實踐）

- **密碼絕不明文儲存**：用 bcrypt/argon2 雜湊（+ salt），別用 MD5/SHA、別自己實作（見 [密碼雜湊](../20-security-system-design/08-password-hashing.md)）。
- **分清認證（401，你是誰）與授權（403，能做什麼）**：先認證再授權。
- **API/微服務用 JWT token**（無狀態、易擴展）；傳統 Web 用 session（易撤銷）（見 [JWT](../20-security-system-design/04-jwt.md)）。
- **FastAPI 用 `Depends` 實作認證授權**（`Depends(get_current_user)`、`Depends(require_role)`，見 [Depends](11-fastapi-depends.md)）。
- **授權要檢查資源擁有權**：不只檢查角色，還要「只能存取自己的資料」。
- **密鑰/JWT SECRET 用環境變數**（見 [密鑰管理](../20-security-system-design/05-secrets-management.md)），別寫死。
- **用 HTTPS**：token/cookie 明文傳輸會被竊聽。

## Common Mistakes（常見誤解）

- **明文儲存密碼**：外洩災難；用雜湊。這是最嚴重的錯誤。
- **用快速雜湊（MD5/SHA）存密碼**：易被暴力破解；用 bcrypt/argon2（慢、有 salt）。
- **混淆認證與授權**：401（未認證）vs 403（未授權）用錯。
- **JWT 沒驗證簽章就信任**：任何人可偽造；一定驗證簽章（見 [JWT](../20-security-system-design/04-jwt.md)）。
- **授權只檢查角色不檢查擁有權**：admin 以外的越權（看別人的資料）。
- **SECRET/密鑰寫死在程式**：外洩風險；用環境變數。
- **不用 HTTPS**：token/密碼明文傳輸被竊聽。
- **JWT 存敏感資訊**：JWT payload 是 base64 編碼（非加密），別放密碼等。

## Interview Notes（面試重點）

- **能清楚區分認證（authn，你是誰，401）vs 授權（authz，能做什麼，403）**，先認證再授權——高頻考點。
- **知道密碼絕不明文儲存，用 bcrypt/argon2 雜湊（+salt、單向、驗證時比對）**，別用 MD5/SHA。
- **能對比 JWT（無狀態、易擴展、難撤銷、適合 API）vs Session（有狀態、易撤銷、適合傳統 Web）**。
- 知道 FastAPI 用 **`Depends` 實作認證授權**（`get_current_user`、`require_role`）。
- 知道**授權要檢查資源擁有權**（不只角色）、JWT 要驗證簽章、SECRET 用環境變數、用 HTTPS。

---

➡️ 下一章：[模板與靜態檔](10-templates.md)

[⬆️ 回 Part 14 索引](README.md)
