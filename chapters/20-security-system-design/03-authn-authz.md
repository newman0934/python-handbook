# 認證與授權

> 「你是誰？」和「你能做什麼？」是兩個不同的問題，卻常被混為一談。**認證（authentication）** 確認身分、**授權（authorization）** 決定權限。搞混或做錯任一個，都是嚴重的資安漏洞。這章講兩者的分野、常見機制，以及 RBAC 權限模型。

## 💡 白話導讀（建議先讀）

住飯店的兩道關卡,順序固定:

1. **櫃檯 check-in 驗證件**——確認「你是不是訂房的那個人」。這是**認證（authentication，authN）**。
2. **房卡只開得了你的房**——確認「你能進哪些門」。這是**授權（authorization，authZ）**。

兩個問題完全不同,卻常被混為一談。工程上的鐵律:**先認證,再授權**;
而最常見的漏洞是「只做了認證、忘了授權」——查了證件就發萬能房卡:
使用者 A 登入後,把 URL 裡的 `/orders/42` 改成 `/orders/43`,
竟然看得到別人的訂單（這叫 **IDOR**,OWASP 常客）。
教訓:**每個資源存取都要問「這個人有權看『這一筆』嗎」**,不只是「他登入了嗎」。

認證的強度靠**因素（factor）**疊加:你知道的（密碼）＋你擁有的（手機 OTP）＋
你本身的（指紋）——MFA 就是「偷到密碼也缺第二把鑰匙」。

授權的組織方式主流兩種:**RBAC**（照職位發權限:admin/editor/viewer,簡單好管）
與 **ABAC**（照屬性判斷:「文件擁有者或同部門主管可讀」,靈活但複雜）。

這章用 FastAPI 依賴注入實作整條鏈:登入發 token（下一章 [JWT](04-jwt.md) 細講）、
路由層驗身分、資源層驗權限——並示範 IDOR 的錯誤與修正對照。

## Why（為什麼）

每個有使用者的系統都要回答兩個問題：

1. **「你是誰？」**——使用者宣稱自己是 alice，你怎麼確認？這是**認證（authentication，authN）**。
2. **「你能做什麼？」**——確認是 alice 後，她能不能刪除別人的貼文、能不能看管理後台？這是**授權（authorization，authZ）**。

這兩者**必須都做對**，缺一不可：

- 只有認證沒授權：確認了身分，卻讓每個登入者都能做任何事——一般使用者能刪別人資料、看到管理功能。
- 認證做錯：身分能被偽造，攻擊者假冒任何人。
- 授權做錯（**broken access control**，常年 OWASP Top 1）：能透過改個 URL 參數（`/orders/123` → `/orders/124`）看別人的訂單、越權操作。

現實中的重大資料外洩，很多不是「密碼被破」，而是**授權沒做好**——系統認得你是誰，卻沒檢查「你有沒有權限存取這筆資料」。這章講清楚認證與授權的分野、常見機制（session、token、[JWT](04-jwt.md)），以及 **RBAC（角色權限）** 這個最常用的授權模型。密碼本身怎麼安全儲存見 [密碼雜湊](08-password-hashing.md)。

## Theory（理論：authN vs authZ）

**認證（authentication）**——驗證「你是不是你宣稱的那個人」。方式（authentication factors）：

- **你知道的**（something you know）：密碼、PIN。
- **你擁有的**（something you have）：手機（OTP）、硬體金鑰、憑證。
- **你本身的**（something you are）：指紋、臉部等生物特徵。
- **MFA（多因素認證）**：組合多種（如密碼 + 手機 OTP），大幅提升安全——就算密碼外洩，攻擊者也缺第二因素。

**授權（authorization）**——確認身分後，決定「這個身分能存取什麼、能做什麼」。常見模型：

- **RBAC（Role-Based Access Control，角色權限）**：使用者被賦予**角色**（admin、editor、viewer），角色綁定**權限**（permission）。檢查「使用者的角色是否擁有此權限」。最常用、好管理。
- **ABAC（Attribute-Based，屬性權限）**：依屬性/情境動態判斷（部門、時間、資源擁有者），更細緻但更複雜。
- **ACL（Access Control List）**：每個資源列出誰能存取。

**順序**：**先認證、後授權**——必須先知道你是誰，才能判斷你能做什麼。

## Specification（規範：認證機制與授權檢查）

**認證後如何「記住」登入狀態**（HTTP 無狀態，見 [Web](../14-web/README.md)）：

- **Session（伺服器端狀態）**：登入後伺服器建立 session、存 session 資料（在記憶體/Redis/DB），回一個 **session id** 給瀏覽器（存 cookie）。之後每個請求帶 session id，伺服器查出對應使用者。狀態在伺服器 → 可即時撤銷，但需共享儲存（見 [12-factor](../19-cloud-native/04-12-factor.md)）。
- **Token（客戶端狀態，如 [JWT](04-jwt.md)）**：登入後發一個**簽章的 token** 給客戶端，token 本身**攜帶**使用者資訊。之後每個請求帶 token（通常 `Authorization: Bearer <token>`），伺服器**驗簽**即信任，無需查儲存。無狀態、易擴展，但撤銷較麻煩（見 [JWT](04-jwt.md)）。

**授權檢查（RBAC）**：

```python
# 每個受保護的操作都檢查權限
def delete_post(user, post_id):
    if not user.has_permission("post:delete"):
        raise PermissionDenied()
    ...

# 資源層級授權：不只檢查「能刪貼文」，還要檢查「能刪這一篇」
def delete_post(user, post):
    if post.author_id != user.id and not user.has_permission("post:delete_any"):
        raise PermissionDenied()   # 防越權存取別人的資源
```

**框架整合**：FastAPI 用依賴注入（`Depends`）做認證/授權，把「取得當前使用者 + 檢查權限」封裝成可重用的依賴（見 [FastAPI](../14-web/README.md)）。

## Implementation（底層：session vs token、授權的位置）

**session vs token 的權衡**：

- **Session**：狀態在伺服器。伺服器隨時能**撤銷**（刪掉 session）——登出、封鎖立即生效。代價是每個請求要查 session 儲存，且多實例需共享儲存（Redis）。
- **Token（JWT）**：狀態在客戶端、簽章保證不被竄改。伺服器**無需查儲存**（驗簽即可）→ 無狀態、易水平擴展、適合微服務。代價是**難即時撤銷**——token 在過期前一直有效，要撤銷得靠短期效期 + refresh token，或維護黑名單（就又引入了狀態）。這是常考的取捨。

**授權必須在「每次存取」都檢查、且在伺服器端**：最常見的致命錯誤是**只靠前端隱藏功能**（不顯示刪除按鈕）就以為安全了——攻擊者直接打 API 就繞過。授權**必須在後端、在每個受保護操作**強制檢查。同樣地，**別在 URL/請求裡信任客戶端傳來的角色/權限**（`?is_admin=true`）——權限要從**伺服器端的使用者記錄**查，不是客戶端說了算。

**IDOR（Insecure Direct Object Reference，不安全的直接物件引用）**——broken access control 的典型：`GET /orders/124` 直接用 URL 裡的 id 撈資料，卻沒檢查「這筆訂單是不是屬於當前使用者」。攻擊者改個數字就看到別人的訂單。防禦：**資源層級授權**——不只檢查「能不能看訂單」（功能權限），還要檢查「能不能看**這一筆**」（資源歸屬），如上面 `post.author_id != user.id` 的檢查。

**最小權限原則（principle of least privilege）**：每個使用者/角色/服務只給**完成工作所需的最小權限**，不多給。萬一某帳號被攻破，損害也受限。

## Code Example（可執行的 Python 範例）

```python
# rbac_demo.py — RBAC 授權與資源層級檢查（純標準庫，可執行）
from __future__ import annotations

from dataclasses import dataclass


class PermissionDenied(Exception):
    """授權失敗（對應 HTTP 403）。"""


# 角色 → 權限的對應（RBAC 核心）
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"post:read", "post:delete_any", "user:manage"},
    "editor": {"post:read", "post:delete_own"},
    "viewer": {"post:read"},
}


@dataclass(frozen=True)
class User:
    id: int
    role: str

    def has_permission(self, perm: str) -> bool:
        return perm in ROLE_PERMISSIONS.get(self.role, set())


@dataclass(frozen=True)
class Post:
    id: int
    author_id: int


def delete_post(user: User, post: Post) -> str:
    """授權：能刪任何貼文，或只能刪自己的（資源層級檢查，防 IDOR）。"""
    if user.has_permission("post:delete_any"):
        return f"user{user.id}({user.role}) 刪除 post{post.id} ✓"
    if user.has_permission("post:delete_own") and post.author_id == user.id:
        return f"user{user.id}({user.role}) 刪除自己的 post{post.id} ✓"
    raise PermissionDenied(f"user{user.id}({user.role}) 無權刪除 post{post.id}")


def main() -> None:
    admin = User(id=1, role="admin")
    editor = User(id=2, role="editor")
    viewer = User(id=3, role="viewer")
    post_by_editor = Post(id=100, author_id=2)

    # admin 能刪任何人的貼文
    print(delete_post(admin, post_by_editor))
    # editor 能刪自己的貼文
    print(delete_post(editor, post_by_editor))

    # viewer 無刪除權限 → 被擋
    try:
        delete_post(viewer, post_by_editor)
    except PermissionDenied as exc:
        print(f"擋下: {exc}")

    # editor 想刪「別人」的貼文（IDOR 越權）→ 被擋
    post_by_other = Post(id=200, author_id=999)
    try:
        delete_post(editor, post_by_other)
    except PermissionDenied as exc:
        print(f"擋下越權: {exc}")


if __name__ == "__main__":
    main()
```

**預期輸出**：

```pycon
$ python rbac_demo.py
user1(admin) 刪除 post100 ✓
user2(editor) 刪除自己的 post100 ✓
擋下: user3(viewer) 無權刪除 post100
擋下越權: user2(editor) 無權刪除 post200
```

逐段解說：

- **`ROLE_PERMISSIONS`**：RBAC 的核心——角色對應到一組權限。使用者透過角色間接獲得權限，管理起來只需改角色。
- **`has_permission`**：檢查使用者的角色是否含此權限——這是**功能層級**授權。
- **`delete_post` 的兩層檢查**：先看有沒有 `delete_any`（admin 能刪任何人的）；否則看有沒有 `delete_own` **且**貼文是自己的（`post.author_id == user.id`）——這是**資源層級**授權，防 IDOR。
- **viewer 被擋**：沒有任何刪除權限 → `PermissionDenied`（HTTP 403）。
- **editor 越權被擋**：editor 有 `delete_own`，但貼文 200 的作者是別人（999）→ 資源歸屬檢查失敗，被擋。**這正是防 IDOR 的關鍵**——不只檢查「能刪貼文」，還檢查「能刪**這一篇**」。
- **要點**：授權要在伺服器端、每次存取檢查，且涵蓋功能權限與資源歸屬兩層。

## Diagram（圖解：認證 → 授權流程）

```mermaid
flowchart TD
    R["請求(帶 session/token)"] --> AUTHN{"認證<br/>你是誰?"}
    AUTHN -->|身分無效| E401["401 Unauthorized"]
    AUTHN -->|確認身分| AUTHZ{"授權<br/>你能做這個嗎?"}
    AUTHZ -->|功能權限不足| E403a["403 Forbidden"]
    AUTHZ -->|資源不屬於你(IDOR)| E403b["403 Forbidden"]
    AUTHZ -->|通過| OK["執行操作"]
    style AUTHN fill:#e3f2fd
    style AUTHZ fill:#fff3e0
    style OK fill:#e8f5e9
    style E401 fill:#ffebee
```

## Best Practice（最佳實踐）

- **分清認證（你是誰）與授權（你能做什麼），兩者都要做對**。
- **授權在伺服器端、每次存取檢查**：絕不只靠前端隱藏功能。
- **做資源層級授權防 IDOR**：檢查「能操作**這一筆**」（資源歸屬），不只「能操作這類」。
- **用 RBAC 管理權限**：角色綁權限、使用者綁角色，好維護。
- **最小權限原則**：只給必要權限，限縮被攻破後的損害。
- **啟用 MFA**（尤其管理帳號）：密碼外洩仍有第二道防線。
- **權限從伺服器端使用者記錄查**，別信任客戶端傳的角色/旗標。
- **session/token 依需求選型**：需即時撤銷用 session；需無狀態擴展用 [JWT](04-jwt.md) + 短效期。
- **敏感操作記 audit log**（誰、何時、做了什麼，見 [可觀測性](../19-cloud-native/08-observability.md)）。

## Common Mistakes（常見誤解）

- **混淆認證與授權**：以為「登入了」就能做任何事，漏了授權檢查。
- **只靠前端隱藏功能**：不顯示按鈕但 API 沒擋，攻擊者直接打 API 就繞過。
- **IDOR：用 URL 的 id 直接撈資料不檢查歸屬**：改個數字看別人的資料——broken access control。
- **信任客戶端傳的權限**（`?is_admin=true`、token 裡未驗簽的 claim）：權限要伺服器端決定。
- **權限過大 / 沒有最小權限**：一個帳號被攻破就全盤皆輸。
- **JWT 當 session 用卻沒處理撤銷**：登出/封鎖無法即時生效（見 [JWT](04-jwt.md)）。
- **只在部分入口檢查授權**：漏掉某個 API 就是破口；每個受保護操作都要檢查。
- **把授權邏輯散落各處難維護**：集中成可重用的檢查（如 FastAPI 依賴）。

## Interview Notes（面試重點）

- **能清楚區分認證（authN，你是誰）與授權（authZ，你能做什麼）**，並知道順序（先認證後授權）。
- **能說明 session vs token(JWT) 的權衡**：伺服器狀態可即時撤銷 vs 無狀態易擴展但難撤銷。
- **能解釋 RBAC**（角色—權限—使用者）與最小權限原則。
- **能講 broken access control / IDOR** 為何是 OWASP 頭號問題，以及資源層級授權如何防它。
- **知道授權必須在伺服器端、每次存取、涵蓋功能與資源兩層**，別信任客戶端。
- **知道 MFA、audit log** 等強化手段。

---

➡️ 下一章：[JWT](04-jwt.md)

[⬆️ 回 Part 20 索引](README.md)
