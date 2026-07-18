"""Part 16 範例的驗證測試。

執行：pytest examples/part16
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from examples.part16.architecture import (
    Checkout,
    Discount,
    EventBus,
    FixedDiscount,
    IdempotentEmailHandler,
    InMemoryAccountRepository,
    InMemoryOrderStore,
    InMemoryUserRepository,
    Money,
    NoDiscount,
    Order,
    OrderEvents,
    OrderPlaced,
    OrderRecord,
    PercentageDiscount,
    PlaceOrderUseCase,
    Settings,
    TransferService,
    detect_cycle,
    get_pricing,
    load_settings,
    to_bool,
    transfer_endpoint,
)
from examples.part16.architecture import (
    FakeNotificationAdapter as FakeNotifier,
)
from examples.part16.architecture import (
    InsufficientBalanceError as BalanceError,
)
from examples.part16.architecture import (
    UserService as Users,
)


# --- 分層 / Clean：service + 表現層映射（見 01, 02）---
def test_transfer_success() -> None:
    repo = InMemoryAccountRepository({1: 1000, 2: 500})
    service = TransferService(repo)
    status, body = transfer_endpoint(service, 1, 2, 300)
    assert status == 200
    assert body == {"status": "ok"}
    assert repo.get_balance(1) == 700
    assert repo.get_balance(2) == 800


def test_transfer_insufficient_maps_to_400() -> None:
    repo = InMemoryAccountRepository({1: 100, 2: 0})
    service = TransferService(repo)
    status, body = transfer_endpoint(service, 1, 2, 99999)
    assert status == 400
    assert "餘額不足" in body["error"]
    # 領域層拋乾淨的領域例外
    with pytest.raises(BalanceError):
        service.transfer(1, 2, 99999)


# --- DI + Repository：業務規則與可測試性（見 03, 04）---
def test_user_register_and_duplicate_rule() -> None:
    service = Users(InMemoryUserRepository())
    alice = service.register("Alice", "alice@example.com")
    assert alice.id == 1
    bob = service.register("Bob", "bob@example.com")
    assert bob.id == 2
    with pytest.raises(ValueError, match="已被註冊"):
        service.register("Alice2", "alice@example.com")


# --- SOLID：OCP + DIP（見 05）---
@pytest.mark.parametrize(
    ("discount", "expected"),
    [
        (NoDiscount(), 1000.0),
        (PercentageDiscount(20), 800.0),
        (FixedDiscount(150), 850.0),
        (FixedDiscount(5000), 0.0),  # 折到 0 為止，不為負
    ],
)
def test_checkout_discounts(discount: Discount, expected: float) -> None:
    assert Checkout(discount).total(1000.0) == pytest.approx(expected)


# --- 設計模式：Strategy + Factory + Observer（見 06）---
def test_pricing_strategy_factory() -> None:
    assert get_pricing("regular")(1000) == pytest.approx(1000)
    assert get_pricing("member")(1000) == pytest.approx(900)
    assert get_pricing("vip")(1000) == pytest.approx(800)
    with pytest.raises(ValueError, match="未知會員等級"):
        get_pricing("unknown")


def test_observer_notifies_all_subscribers() -> None:
    log: list[str] = []
    events = OrderEvents()
    events.subscribe(lambda e: log.append(f"log: {e}"))
    events.subscribe(lambda e: log.append(f"notify: {e}"))
    events.emit("訂單成立")
    assert log == ["log: 訂單成立", "notify: 訂單成立"]


# --- 專案結構：循環相依偵測（見 07）---
def test_detect_cycle_none_for_acyclic() -> None:
    good = {
        "router": ["service"],
        "service": ["repository"],
        "repository": [],
    }
    assert detect_cycle(good) is None


def test_detect_cycle_finds_cycle() -> None:
    bad = {"a": ["b"], "b": ["a"]}
    cycle = detect_cycle(bad)
    assert cycle is not None
    assert cycle[0] == cycle[-1]  # 循環路徑首尾相同


# --- DDD：Value Object + Aggregate（見 08）---
def test_money_value_equality_and_ops() -> None:
    assert Money(Decimal(100)) == Money(Decimal(100))  # 由值定義相等
    assert (Money(Decimal(100)) + Money(Decimal(50))).amount == Decimal(150)
    assert (Money(Decimal(100)) * 3).amount == Decimal(300)
    with pytest.raises(ValueError, match="幣別不符"):
        _ = Money(Decimal(1), "TWD") + Money(Decimal(1), "USD")


def test_order_aggregate_invariants() -> None:
    order = Order(order_id=1)
    order.add_line("鍵盤", 2, Money(Decimal(1500)))
    order.add_line("滑鼠", 1, Money(Decimal(800)))
    assert order.total().amount == Decimal(3800)
    order.submit()
    assert order.status == "submitted"
    # 不變條件：送出後不能再加項目
    with pytest.raises(ValueError, match="已送出"):
        order.add_line("螢幕", 1, Money(Decimal(5000)))


def test_empty_order_cannot_submit() -> None:
    with pytest.raises(ValueError, match="空訂單"):
        Order(order_id=2).submit()


# --- Hexagonal：ports & adapters（見 09）---
def test_place_order_use_case_with_adapters() -> None:
    store = InMemoryOrderStore()
    notifier = FakeNotifier()
    use_case = PlaceOrderUseCase(store, notifier)
    use_case.execute(OrderRecord(id=1, amount=3800))
    assert store.get(1) == OrderRecord(id=1, amount=3800)
    assert notifier.messages == ["訂單 1 已成立（金額 3800）"]


# --- 事件驅動：event bus + 冪等消費者（見 10）---
def test_event_bus_fans_out_and_idempotent() -> None:
    bus = EventBus()
    email = IdempotentEmailHandler()
    inventory: list[int] = []
    bus.subscribe(email.handle)
    bus.subscribe(lambda e: inventory.append(e.order_id))

    event = OrderPlaced(event_id="evt-1", order_id=100, amount=3800)
    bus.publish(event)
    assert email.sent == [100]
    assert inventory == [100]

    # 至少一次投遞：重複事件，冪等消費者只處理一次
    bus.publish(event)
    assert email.sent == [100]  # 沒重複寄
    assert inventory == [100, 100]  # 非冪等的訂閱者則會重複


# --- 設定管理（見 11）---
def test_to_bool() -> None:
    assert to_bool("true") is True
    assert to_bool("1") is True
    assert to_bool("false") is False
    assert to_bool("") is False


def test_load_settings_layered_override() -> None:
    merged = {"PORT": "5432", "DATABASE_URL": "sqlite:///dev.db", "DEBUG": "true"}
    settings = load_settings(merged)
    assert settings == Settings(database_url="sqlite:///dev.db", port=5432, debug=True)


def test_load_settings_validation() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        load_settings({"PORT": "8000"})
    with pytest.raises(ValueError, match="整數"):
        load_settings({"DATABASE_URL": "x", "PORT": "eighty"})


def test_order_only_depends_on_public_interface() -> None:
    """orders 透過 UsersAPI 取用 users,不碰其內部。"""
    from examples.part16.modular_monolith import LocalUsers, OrderService

    svc = OrderService(LocalUsers())
    assert svc.place_order(1, "書") == "Ada 下單:書"


def test_extracting_to_service_needs_no_business_change() -> None:
    """把 users 換成遠端實作(模擬抽成微服務),OrderService 一行不改照樣運作。"""
    from examples.part16.modular_monolith import (
        LocalUsers,
        OrderService,
        RemoteUsers,
    )

    order = "Ada 下單:書"
    assert OrderService(LocalUsers()).place_order(1, "書") == order
    assert OrderService(RemoteUsers({1: "Ada"})).place_order(1, "書") == order  # 同結果
