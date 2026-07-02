"""Part 14 Web 開發範例：以純邏輯模擬框架行為，不需啟動伺服器即可測試。

涵蓋：路由分派、CORS 檢查、安全 cookie、依賴注入解析、WebSocket 連線管理、
領域例外映射成 HTTP 回應。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


# --- 路由分派（見 05-routing）---
def route_handler(method: str, path: str, routes: dict[tuple[str, str], str]) -> tuple[int, str]:
    """模擬 Web 框架的路由分派：找到對應 handler 或回 404/405。"""
    if (method, path) in routes:
        return 200, routes[(method, path)]
    # 路徑存在但方法不符 → 405
    if any(p == path for _, p in routes):
        return 405, "Method Not Allowed"
    return 404, "Not Found"


# --- CORS 檢查（見 14-cors-cookie-session）---
def check_cors(origin: str, allowed_origins: list[str], with_credentials: bool) -> tuple[bool, str]:
    """模擬 CORS 來源檢查，並標記不安全設定。"""
    if "*" in allowed_origins:
        if with_credentials:
            return True, "危險：allow_origins='*' 配 credentials（CSRF 風險）"
        return True, "允許任何來源"
    if origin in allowed_origins:
        return True, "允許（來源在白名單）"
    return False, "拒絕（跨源被 CORS 擋）"


def build_secure_cookie(name: str, value: str) -> dict[str, object]:
    """建立安全的 cookie 設定：httponly + secure + samesite。"""
    return {
        "key": name,
        "value": value,
        "httponly": True,
        "secure": True,
        "samesite": "lax",
        "max_age": 3600,
    }


# --- 依賴注入解析（見 11-fastapi-depends）---
class DependencyResolver:
    """模擬 FastAPI 的依賴解析，支援測試覆寫（dependency_overrides）。"""

    def __init__(self) -> None:
        self.overrides: dict[Callable[..., Any], Callable[..., Any]] = {}

    def resolve(self, dependency: Callable[..., Any], **kwargs: Any) -> Any:
        actual = self.overrides.get(dependency, dependency)
        return actual(**kwargs)


def pagination(page: int = 1, limit: int = 20) -> dict[str, int]:
    """共用分頁參數依賴。"""
    return {"page": page, "limit": limit, "offset": (page - 1) * limit}


# --- WebSocket 連線管理（見 13-websocket）---
class FakeWebSocket:
    """模擬 WebSocket 連線。"""

    def __init__(self, client_id: str) -> None:
        self.client_id = client_id
        self.received: list[str] = []

    def send(self, message: str) -> None:
        self.received.append(message)


class ConnectionManager:
    """管理 WebSocket 連線並廣播。"""

    def __init__(self) -> None:
        self.active: list[FakeWebSocket] = []

    def connect(self, ws: FakeWebSocket) -> None:
        self.active.append(ws)

    def disconnect(self, ws: FakeWebSocket) -> None:
        if ws in self.active:
            self.active.remove(ws)

    def broadcast(self, message: str) -> None:
        for connection in self.active:
            connection.send(message)


# --- 領域例外與 HTTP 映射（見 16-exception-handlers）---
class DomainError(Exception):
    """領域例外基底（不知道 HTTP）。"""


class UserNotFoundError(DomainError):
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"找不到使用者 {user_id}")


class InsufficientBalanceError(DomainError):
    def __init__(self, needed: int, available: int) -> None:
        self.needed = needed
        self.available = available
        super().__init__("餘額不足")


def map_to_http(exc: Exception) -> tuple[int, dict[str, object]]:
    """例外處理器：領域例外 → (狀態碼, 統一錯誤 body)。"""
    if isinstance(exc, UserNotFoundError):
        return 404, {"error": {"code": "USER_NOT_FOUND", "message": str(exc)}}
    if isinstance(exc, InsufficientBalanceError):
        return 400, {
            "error": {
                "code": "INSUFFICIENT_BALANCE",
                "message": "餘額不足",
                "details": {"needed": exc.needed, "available": exc.available},
            }
        }
    # 未預期的例外：回一般 500，不洩漏細節
    return 500, {"error": {"code": "INTERNAL_ERROR", "message": "伺服器內部錯誤"}}


def transfer(balance: int, amount: int, *, user_exists: bool) -> str:
    """領域邏輯：拋乾淨的領域例外，不含 HTTP。"""
    if not user_exists:
        raise UserNotFoundError(1)
    if balance < amount:
        raise InsufficientBalanceError(amount, balance)
    return "轉帳成功"
