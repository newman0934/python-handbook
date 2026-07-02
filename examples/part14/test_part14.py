"""Part 14 範例的驗證測試。

執行：pytest examples/part14
"""

import pytest

from examples.part14.web import (
    ConnectionManager,
    DependencyResolver,
    FakeWebSocket,
    InsufficientBalanceError,
    UserNotFoundError,
    build_secure_cookie,
    check_cors,
    map_to_http,
    pagination,
    route_handler,
    transfer,
)

ROUTES = {
    ("GET", "/users"): "list_users",
    ("POST", "/users"): "create_user",
    ("GET", "/users/1"): "get_user",
}


@pytest.mark.parametrize(
    ("method", "path", "status"),
    [
        ("GET", "/users", 200),
        ("POST", "/users", 200),
        ("GET", "/missing", 404),
        ("DELETE", "/users", 405),  # 路徑存在但方法不符
    ],
)
def test_route_handler(method: str, path: str, status: int) -> None:
    code, _ = route_handler(method, path, ROUTES)
    assert code == status


def test_cors_whitelist_allows_known_origin() -> None:
    ok, _ = check_cors("https://app.com", ["https://app.com"], with_credentials=True)
    assert ok


def test_cors_blocks_unknown_origin() -> None:
    ok, msg = check_cors("https://evil.com", ["https://app.com"], with_credentials=True)
    assert not ok
    assert "拒絕" in msg


def test_cors_wildcard_with_credentials_is_flagged_dangerous() -> None:
    ok, msg = check_cors("https://evil.com", ["*"], with_credentials=True)
    assert ok
    assert "危險" in msg


def test_secure_cookie_has_safety_attributes() -> None:
    cookie = build_secure_cookie("session_id", "abc123")
    assert cookie["httponly"] is True
    assert cookie["secure"] is True
    assert cookie["samesite"] == "lax"


def test_pagination_dependency() -> None:
    assert pagination(page=2, limit=10) == {"page": 2, "limit": 10, "offset": 10}


def test_dependency_override_injects_mock() -> None:
    resolver = DependencyResolver()
    # 未覆寫：用真的依賴
    assert resolver.resolve(pagination, page=1, limit=20)["offset"] == 0
    # 覆寫（測試用假的）
    resolver.overrides[pagination] = lambda page=1, limit=20: {"page": 99, "limit": 0, "offset": 0}
    assert resolver.resolve(pagination)["page"] == 99


def test_websocket_broadcast_reaches_all_active() -> None:
    manager = ConnectionManager()
    alice, bob, cara = FakeWebSocket("Alice"), FakeWebSocket("Bob"), FakeWebSocket("Cara")
    for ws in (alice, bob, cara):
        manager.connect(ws)

    manager.broadcast("hello")
    assert alice.received == bob.received == cara.received == ["hello"]


def test_websocket_disconnect_stops_receiving() -> None:
    manager = ConnectionManager()
    bob, cara = FakeWebSocket("Bob"), FakeWebSocket("Cara")
    manager.connect(bob)
    manager.connect(cara)

    manager.disconnect(cara)
    manager.broadcast("after")
    assert bob.received == ["after"]
    assert cara.received == []  # 斷線後收不到


def test_transfer_success() -> None:
    assert transfer(1000, 500, user_exists=True) == "轉帳成功"


def test_transfer_user_not_found_maps_to_404() -> None:
    with pytest.raises(UserNotFoundError) as exc_info:
        transfer(1000, 500, user_exists=False)
    status, body = map_to_http(exc_info.value)
    assert status == 404
    assert body["error"]["code"] == "USER_NOT_FOUND"  # type: ignore[index]


def test_transfer_insufficient_balance_maps_to_400() -> None:
    with pytest.raises(InsufficientBalanceError) as exc_info:
        transfer(100, 500, user_exists=True)
    status, body = map_to_http(exc_info.value)
    assert status == 400
    assert body["error"]["details"] == {"needed": 500, "available": 100}  # type: ignore[index]


def test_unexpected_exception_maps_to_generic_500() -> None:
    status, body = map_to_http(RuntimeError("DB 連線失敗，密碼是 secret"))
    assert status == 500
    assert body["error"]["code"] == "INTERNAL_ERROR"  # type: ignore[index]
    # 不洩漏內部細節
    assert "secret" not in str(body)
