"""Part 21 範例的驗證測試。

執行：pytest examples/part21
"""

from __future__ import annotations

import pytest

from examples.part21.microservices import (
    CircuitBreaker,
    CircuitOpenError,
    ConfigCenter,
    FeatureFlags,
    Gateway,
    HealthChecker,
    MessageBroker,
    OrderService,
    RoundRobinBalancer,
    ServiceRegistry,
    UserService,
    binary_size,
    encode_varint,
    json_size,
)


# --- 服務邊界（見 01）---
def test_service_boundary_via_api() -> None:
    users = UserService()
    users.create_user(1, "alice")
    orders = OrderService(users=users)
    assert orders.place_order(1, 500)["user"] == "alice"
    with pytest.raises(ValueError, match="不存在"):
        orders.place_order(999, 100)


# --- 非同步通訊：下游掛不影響上游（見 03）---
def test_async_decoupling() -> None:
    broker = MessageBroker()
    broker.publish("order placed")  # 發訊息就返回
    down = {"healthy": False}
    # 下游掛掉：訊息留在佇列
    assert broker.consume_all(lambda m: down["healthy"]) == 0
    assert len(broker.queue) == 1
    # 下游恢復：補處理
    down["healthy"] = True
    assert broker.consume_all(lambda m: down["healthy"]) == 1
    assert len(broker.queue) == 0


# --- 服務發現（見 04）---
def test_service_discovery_health_filter() -> None:
    reg = ServiceRegistry(ttl=10.0)
    for addr in ("10.0.1.3", "10.0.1.7", "10.0.2.1"):
        reg.register("inventory", addr, now=0.0)
    assert reg.discover("inventory", now=1.0) == ["10.0.1.3", "10.0.1.7", "10.0.2.1"]
    reg.set_health("inventory", "10.0.1.7", healthy=False)
    assert reg.discover("inventory", now=1.0) == ["10.0.1.3", "10.0.2.1"]
    # 超過 TTL 沒心跳 → 全部剔除
    assert reg.discover("inventory", now=20.0) == []


def test_round_robin() -> None:
    lb = RoundRobinBalancer()
    instances = ["a", "b", "c"]
    assert [lb.pick(instances) for _ in range(4)] == ["a", "b", "c", "a"]


# --- API gateway（見 05）---
def test_gateway_auth_and_routing() -> None:
    gw = Gateway(
        routes={"/api/orders": "order-service", "/api/users": "user-service"},
        valid_tokens={"valid"},
        rate_limit=10,
    )
    assert gw.handle("/api/orders/1", None) == (401, "Unauthorized")  # 認證先擋(不計數)
    assert gw.handle("/api/orders/1", "valid") == (200, "order-service")
    assert gw.handle("/api/users/5", "valid") == (200, "user-service")
    assert gw.handle("/api/unknown", "valid")[0] == 404


def test_gateway_rate_limit() -> None:
    gw = Gateway(routes={"/api": "svc"}, valid_tokens={"valid"}, rate_limit=2)
    assert gw.handle("/api/x", "valid")[0] == 200  # 1
    assert gw.handle("/api/x", "valid")[0] == 200  # 2
    assert gw.handle("/api/x", "valid") == (429, "Too Many Requests")  # 3 > 2


# --- 健康檢查：liveness 淺 / readiness 深（見 06）---
def test_health_liveness_vs_readiness() -> None:
    db_ok = {"v": True}
    checker = HealthChecker(started=True, critical_deps={"db": lambda: db_ok["v"]})
    assert checker.liveness() is True
    assert checker.readiness() is True
    # DB 斷線：readiness 失敗但 liveness 仍 True（不重啟）
    db_ok["v"] = False
    assert checker.liveness() is True
    assert checker.readiness() is False
    # 啟動中：未就緒
    assert HealthChecker(started=False).readiness() is False


# --- 熔斷器：三態（見 07）---
def test_circuit_breaker_states() -> None:
    cb = CircuitBreaker(fail_threshold=3, recovery_time=5.0)

    def failing() -> str:
        raise ConnectionError("down")

    def working() -> str:
        return "ok"

    for _ in range(3):
        with pytest.raises(ConnectionError):
            cb.call(failing, now=0.0)
    assert cb.state == "open"
    # open 期間快速失敗（不呼叫下游）
    with pytest.raises(CircuitOpenError):
        cb.call(working, now=1.0)
    # 過恢復期 → half-open 試探成功 → closed
    assert cb.call(working, now=6.0) == "ok"
    assert cb.state == "closed"


def test_circuit_breaker_half_open_fail_reopens() -> None:
    cb = CircuitBreaker(fail_threshold=2, recovery_time=5.0)

    def failing() -> str:
        raise ConnectionError("down")

    for _ in range(2):
        with pytest.raises(ConnectionError):
            cb.call(failing, now=0.0)
    assert cb.state == "open"
    # 過恢復期試探又失敗 → 重新 open
    with pytest.raises(ConnectionError):
        cb.call(failing, now=6.0)
    assert cb.state == "open"


# --- 服務治理：集中設定 + feature flag（見 08）---
def test_config_center_dynamic_update() -> None:
    config = ConfigCenter()
    config.set("rate_limit", 100)
    applied = {"rate_limit": config.get("rate_limit")}
    config.watch("rate_limit", lambda v: applied.update(rate_limit=v))
    config.set("rate_limit", 50)  # 動態更新
    assert applied["rate_limit"] == 50


def test_feature_flag_canary_and_killswitch() -> None:
    flags = FeatureFlags()
    flags.set_rollout("new_checkout", 10)
    enabled = sum(flags.is_enabled("new_checkout", u) for u in range(100))
    assert enabled == 10  # 10% 金絲雀
    # 確定性：同使用者結果一致
    assert flags.is_enabled("new_checkout", 5) == flags.is_enabled("new_checkout", 5)
    flags.set_rollout("new_checkout", 0)  # kill switch
    assert sum(flags.is_enabled("new_checkout", u) for u in range(100)) == 0


# --- protobuf 編碼（見 02）---
def test_varint_length() -> None:
    assert len(encode_varint(5)) == 1
    assert len(encode_varint(300)) == 2
    assert len(encode_varint(100000)) == 3


def test_binary_smaller_than_json() -> None:
    j = json_size(12345, "alice", True)
    b = binary_size(12345, "alice", True)
    assert b < j  # 二進位比 JSON 小
    assert j == 44
    assert b == 12
