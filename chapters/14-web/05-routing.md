# 路由與請求處理

> 同一個 `/users/1`，GET 是查、DELETE 是刪——FastAPI 怎麼知道把哪個請求交給哪個函式？而一個 `user_id`，它憑什麼判定是路徑參數、還是 query、還是 body？這章講路由的判定規則。

## 💡 白話導讀（建議先讀）

FastAPI 端點的參數,資料可能來自三個地方——它怎麼知道去哪抓？

**分揀規則**簡單到三行：

```text
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,          # ① 名字出現在路徑 {} 裡 → 從「URL 路徑」抓
    page: int = 1,         # ② 簡單型別、不在路徑裡 → 從「query string」抓(?page=2)
    filters: FilterModel,  # ③ pydantic 模型 → 從「JSON body」抓
): ...
```

背下來：**路徑裡的=路徑參數;pydantic=body;剩下的簡單型別=query**。

三種參數的語意也有慣例:

- **路徑參數**——資源的**身分**(`/users/42`:哪一個)
- **query 參數**——**篩選與選項**(`?page=2&sort=name`:怎麼看)
- **body**——**要提交的資料**(建立/修改的內容)

其餘就是路由的日常件:HTTP 方法對應裝飾器(`@app.get/post/put/delete`)、`APIRouter` 把路由拆檔組織(大專案必用,[task-api](../../project/) 就這麼拆)、路徑參數帶驗證(`Path(gt=0)`)。

一個排序陷阱先提:**固定路徑要放在動態路徑前面**——`/users/me` 若排在 `/users/{id}` 後面,me 會被當成 id 吃掉。

## Why（為什麼）

一個 API 有很多端點（`GET /users`、`POST /users`、`GET /users/{id}`…）——**路由**決定「哪個請求對應哪個處理函式」。FastAPI 依型別註記自動判定「這個參數是路徑參數、query 參數、還是 body」。搞混會拿不到預期的資料。而大型 API 的路由要組織（別塞一個檔）——用 `APIRouter` 分模組。這章講清楚 FastAPI 的路由與請求處理細節，是 [FastAPI 基礎](04-fastapi-basics.md) 的深入。

## Theory（理論：參數的判定規則）

FastAPI 依**參數的來源與型別**分揀資料來源：

1. **路徑參數**：名字出現在路徑 `{...}` 裡 → 從 URL 路徑抓（`/users/{id}` 的 `id`）——資源的身分。
2. **query 參數**：非路徑、非 pydantic 模型的簡單型別（str/int/bool⋯⋯）→ 從 query string 抓（`?key=value`）——篩選與選項。
3. **請求 body**：pydantic 模型（見 [pydantic](06-pydantic-validation.md)）→ 從 JSON body 抓——提交的資料。
4. **特殊**：`Header`/`Cookie`/`Depends` 等明確宣告的來源。

口訣：**在路徑裡＝路徑參數；pydantic 模型＝body；其餘簡單型別＝query**。

## Specification（規範：各種參數）

```python
from fastapi import FastAPI, Query, Path, Header
from pydantic import BaseModel

app = FastAPI()

# 路徑參數
@app.get("/users/{user_id}")
def get_user(user_id: int):            # 路徑參數
    ...

# query 參數（簡單型別）
@app.get("/search")
def search(q: str, page: int = 1, active: bool = True):   # 全 query
    ...

# query 參數 + 驗證（Query）
@app.get("/items")
def list_items(
    limit: int = Query(default=10, le=100),       # <= 100
    keyword: str = Query(default="", min_length=2),
):
    ...

# 路徑 + query + body 混合
@app.put("/users/{user_id}")
def update_user(
    user_id: int,                       # 路徑
    notify: bool = False,               # query
    user: UserUpdate = ...,             # body（pydantic 模型）
):
    ...

# 標頭
@app.get("/protected")
def protected(authorization: str = Header(...)):   # 從標頭抓
    ...
```

## Implementation（參數判定、驗證、APIRouter、路由順序）

### 路徑 vs query vs body 的判定

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.post("/categories/{cat_id}/items")
def create_item(
    cat_id: int,          # 在路徑 {cat_id} → 路徑參數
    dry_run: bool = False,  # 簡單型別、非路徑 → query（?dry_run=true）
    item: Item = ...,       # pydantic 模型 → body（JSON）
):
    return {"category": cat_id, "dry_run": dry_run, "item": item.model_dump()}
# POST /categories/5/items?dry_run=true  + JSON body {"name":..., "price":...}
```

FastAPI 自動分辨：`cat_id`（路徑）、`dry_run`（query）、`item`（body）——依「是否在路徑 / 是否 pydantic 模型」判定。

### 參數驗證：Query / Path

用 `Query`/`Path` 加驗證約束（範圍、長度、正則）：

```python
from fastapi import Query, Path

@app.get("/products")
def list_products(
    page: int = Query(default=1, ge=1),              # >= 1
    size: int = Query(default=20, ge=1, le=100),     # 1-100
    q: str | None = Query(default=None, max_length=50),
):
    ...

@app.get("/users/{user_id}")
def get_user(user_id: int = Path(ge=1)):             # user_id >= 1
    ...
```

不符約束 FastAPI 自動回 **422**——不必手動驗證。約束也會顯示在自動文件裡。

### APIRouter：組織路由

大型 API 的路由用 **`APIRouter`** 分模組（類似 Flask 的 Blueprint）：

```python
# routers/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def list_users():
    return {"users": []}

@router.get("/{user_id}")
def get_user(user_id: int):
    return {"id": user_id}

# main.py
from fastapi import FastAPI
from routers import users

app = FastAPI()
app.include_router(users.router)      # 掛上 /users/... 路由
```

`APIRouter` 讓路由分模組（users、posts、auth 各一檔）、有共同 `prefix`（URL 前綴）與 `tags`（文件分組）——大型 API 的組織方式（也是分層架構的一環，見 [分層架構](../16-architecture/01-layered-architecture.md)）。

### 路由順序：具體在前

FastAPI 依**定義順序**比對路由——**具體路徑要放在通用路徑之前**，否則被通用的攔截：

```python
# ❌ 順序錯：/users/me 被 /users/{id} 攔截（me 被當成 id）
@app.get("/users/{user_id}")
def get_user(user_id: int): ...

@app.get("/users/me")           # 永遠到不了！
def get_me(): ...

# ✅ 具體在前
@app.get("/users/me")           # 先定義具體路徑
def get_me(): ...

@app.get("/users/{user_id}")    # 再定義參數路徑
def get_user(user_id: int): ...
```

固定路徑（`/users/me`）放在參數路徑（`/users/{id}`）之前——否則 `me` 會被當成 `user_id`（然後 int 轉換失敗）。

## Code Example（可執行的 Python 範例）

```python
# routing_demo.py — 展示路由參數判定邏輯（可獨立測試）
from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError


class ItemCreate(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)


def classify_param(name: str, path_template: str, is_model: bool) -> str:
    """模擬 FastAPI 判定參數來源。"""
    if f"{{{name}}}" in path_template:  # 在路徑裡
        return "path"
    if is_model:  # pydantic 模型
        return "body"
    return "query"  # 其餘簡單型別


def validate_query_page(page: int) -> tuple[bool, str]:
    """模擬 Query(ge=1) 驗證。"""
    if page < 1:
        return False, "page 必須 >= 1（422）"
    return True, "OK"


def demo() -> None:
    # 參數判定
    path = "/categories/{cat_id}/items"
    print("參數來源判定（POST /categories/{cat_id}/items）：")
    print(f"  cat_id: {classify_param('cat_id', path, False)}")
    print(f"  dry_run: {classify_param('dry_run', path, False)}")
    print(f"  item(模型): {classify_param('item', path, True)}")

    # query 驗證
    print(f"\nquery 驗證: page=0 → {validate_query_page(0)[1]}")
    print(f"query 驗證: page=1 → {validate_query_page(1)[1]}")

    # body 驗證
    try:
        ItemCreate(name="Book", price=100)
        print("\nbody 驗證: name=Book, price=100 → 通過")
    except ValidationError:
        print("\nbody 驗證失敗")

    print("\n重點：路徑{}→path、pydantic模型→body、其餘→query；具體路由在前")


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python routing_demo.py
參數來源判定（POST /categories/{cat_id}/items）：
  cat_id: path
  dry_run: query
  item(模型): body

query 驗證: page=0 → page 必須 >= 1（422）
query 驗證: page=1 → OK

body 驗證: name=Book, price=100 → 通過

重點：路徑{}→path、pydantic模型→body、其餘→query；具體路由在前
```

## Diagram（圖解：參數判定）

```mermaid
flowchart TD
    A[函式參數] --> B{在路徑 {} 裡?}
    B -- 是 --> C[路徑參數]
    B -- 否 --> D{是 pydantic 模型?}
    D -- 是 --> E[請求 body]
    D -- 否 --> F[query 參數]
    style C fill:#e8f5e9
    style E fill:#e8f5e9
    style F fill:#e8f5e9
```

## Best Practice（最佳實踐）

- **理解參數判定**：路徑 `{}` → 路徑參數、pydantic 模型 → body、其餘簡單型別 → query。
- **用 `Query`/`Path` 加驗證約束**（範圍、長度）：自動回 422、顯示在文件。
- **大型 API 用 `APIRouter` 分模組**（prefix + tags），別把路由塞一個檔。
- **具體路由放在參數路由之前**（`/users/me` 在 `/users/{id}` 前），避免被攔截。
- **用 `tags` 讓自動文件分組**（見 [FastAPI 基礎](04-fastapi-basics.md)）。
- **路由對應 REST 資源**（見 [REST](08-rest-api.md)）：`/users`、`/users/{id}`、方法對應操作。
- **共用邏輯（認證、DB）用 `Depends`**（見 [Depends](11-fastapi-depends.md)）而非在每個路由重複。

## Common Mistakes（常見誤解）

- **搞混參數來源**：以為簡單型別是 body（其實是 query）、或 pydantic 模型是 query（其實是 body）。
- **路由順序錯**：`/users/{id}` 在 `/users/me` 前，`me` 被當 id → 錯誤。
- **所有路由塞一個檔**：大 API 難維護；用 APIRouter 分模組。
- **不加參數驗證**：手動檢查 query 範圍；用 `Query(ge=, le=)` 讓 FastAPI 做。
- **在每個路由重複認證/DB 邏輯**：用 `Depends` 抽出（見 [Depends](11-fastapi-depends.md)）。
- **query 參數沒設預設值卻想選用**：無預設 = 必填；選用要給預設。

## Interview Notes（面試重點）

- **能說出 FastAPI 的參數判定**：**路徑 `{}` → 路徑參數、pydantic 模型 → body、其餘簡單型別 → query**。
- 知道 **`Query`/`Path` 加驗證約束**（自動 422）、**`APIRouter` 組織路由**（prefix + tags）。
- **知道路由順序：具體路徑要放參數路徑之前**（`/users/me` vs `/users/{id}`）——常見陷阱。
- 知道路由對應 REST 資源、共用邏輯用 `Depends`（連結相關章）。
- 知道 query 參數有預設 = 選用、無預設 = 必填。

---

➡️ 下一章：[pydantic 驗證](06-pydantic-validation.md)

[⬆️ 回 Part 14 索引](README.md)
