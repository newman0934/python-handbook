"""Part 16 架構與設計範例：把各章核心邏輯抽成可測的純函式/類別。

涵蓋：分層/依賴反轉、DI 與可測試性、Repository 模式、SOLID(OCP+DIP)、
設計模式(Strategy/Factory/Observer)、循環相依偵測、DDD(Value Object/Aggregate)、
Hexagonal(ports & adapters)、事件驅動(event bus + 冪等消費者)、設定管理。

全部純 stdlib，不需外部服務即可測試。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


# ===== 分層 / Clean（見 01, 02）：service 依賴抽象 repo，領域例外 → 狀態碼 =====
class AccountRepository(Protocol):
    def get_balance(self, account_id: int) -> int: ...
    def update_balance(self, account_id: int, delta: int) -> None: ...


class InsufficientBalanceError(Exception):
    """領域例外（不含 HTTP 概念）。"""


class InMemoryAccountRepository:
    def __init__(self, balances: dict[int, int]) -> None:
        self._balances = balances

    def get_balance(self, account_id: int) -> int:
        return self._balances[account_id]

    def update_balance(self, account_id: int, delta: int) -> None:
        self._balances[account_id] += delta


class TransferService:
    """業務層：純規則，只依賴 repo 抽象，不知道 HTTP/DB 細節。"""

    def __init__(self, repo: AccountRepository) -> None:
        self._repo = repo

    def transfer(self, from_id: int, to_id: int, amount: int) -> None:
        if self._repo.get_balance(from_id) < amount:
            raise InsufficientBalanceError("餘額不足")
        self._repo.update_balance(from_id, -amount)
        self._repo.update_balance(to_id, amount)


def transfer_endpoint(
    service: TransferService, from_id: int, to_id: int, amount: int
) -> tuple[int, dict[str, str]]:
    """表現層：把領域例外映射成 HTTP 狀態碼（這裡用 tuple 模擬回應）。"""
    try:
        service.transfer(from_id, to_id, amount)
        return 200, {"status": "ok"}
    except InsufficientBalanceError as exc:
        return 400, {"error": str(exc)}


# ===== DI + Repository（見 03, 04）：建構子注入、可換假實作測試 =====
@dataclass
class User:
    id: int
    name: str
    email: str


class UserRepository(Protocol):
    def get(self, user_id: int) -> User | None: ...
    def add(self, user: User) -> None: ...
    def find_by_email(self, email: str) -> User | None: ...


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._users: dict[int, User] = {}

    def get(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def add(self, user: User) -> None:
        self._users[user.id] = user

    def find_by_email(self, email: str) -> User | None:
        return next((u for u in self._users.values() if u.email == email), None)


class UserService:
    """業務層：透過 repo 抽象操作，不含 SQL；email 不重複的規則屬純業務。"""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo
        self._next_id = 1

    def register(self, name: str, email: str) -> User:
        if self._repo.find_by_email(email):
            raise ValueError(f"email {email} 已被註冊")
        user = User(id=self._next_id, name=name, email=email)
        self._repo.add(user)
        self._next_id += 1
        return user


# ===== SOLID：OCP + DIP（見 05）：加折扣 = 加類別，Checkout 依賴抽象 =====
class Discount(ABC):
    @abstractmethod
    def apply(self, price: float) -> float: ...


class NoDiscount(Discount):
    def apply(self, price: float) -> float:
        return price


class PercentageDiscount(Discount):
    def __init__(self, percent: float) -> None:
        self._percent = percent

    def apply(self, price: float) -> float:
        return price * (1 - self._percent / 100)


class FixedDiscount(Discount):
    def __init__(self, amount: float) -> None:
        self._amount = amount

    def apply(self, price: float) -> float:
        return max(0.0, price - self._amount)


class Checkout:
    def __init__(self, discount: Discount) -> None:
        self._discount = discount

    def total(self, price: float) -> float:
        return self._discount.apply(price)


# ===== 設計模式：Strategy + Factory + Observer（見 06）=====
def regular_price(price: float) -> float:
    return price


def member_price(price: float) -> float:
    return price * 0.9


def vip_price(price: float) -> float:
    return price * 0.8


def get_pricing(tier: str) -> Callable[[float], float]:
    """Factory：以字典分派選出 Strategy（函式即策略）。"""
    strategies: dict[str, Callable[[float], float]] = {
        "regular": regular_price,
        "member": member_price,
        "vip": vip_price,
    }
    try:
        return strategies[tier]
    except KeyError:
        raise ValueError(f"未知會員等級: {tier}") from None


class OrderEvents:
    """Observer：一對多事件通知。"""

    def __init__(self) -> None:
        self._handlers: list[Callable[[str], None]] = []

    def subscribe(self, handler: Callable[[str], None]) -> None:
        self._handlers.append(handler)

    def emit(self, event: str) -> None:
        for handler in self._handlers:
            handler(event)


# ===== 專案結構：循環相依偵測（見 07）=====
def detect_cycle(deps: dict[str, list[str]]) -> list[str] | None:
    """偵測模組依賴圖中的循環（DFS）。回傳循環路徑或 None。"""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = dict.fromkeys(deps, WHITE)
    path: list[str] = []

    def visit(node: str) -> list[str] | None:
        color[node] = GRAY
        path.append(node)
        for dep in deps.get(node, []):
            if color.get(dep, WHITE) == GRAY:  # 遇到灰色節點 → 循環
                return [*path[path.index(dep) :], dep]
            if color.get(dep, WHITE) == WHITE:
                cycle = visit(dep)
                if cycle:
                    return cycle
        color[node] = BLACK
        path.pop()
        return None

    for node in deps:
        if color[node] == WHITE:
            cycle = visit(node)
            if cycle:
                return cycle
    return None


# ===== DDD：Value Object + Aggregate + 不變條件（見 08）=====
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "TWD"

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError("幣別不符")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, qty: int) -> Money:
        return Money(self.amount * qty, self.currency)


@dataclass(frozen=True)
class OrderLine:
    product: str
    quantity: int
    unit_price: Money

    def subtotal(self) -> Money:
        return self.unit_price * self.quantity


class Order:
    """Aggregate Root：維護內部一致性與不變條件。"""

    def __init__(self, order_id: int) -> None:
        self.id = order_id
        self._lines: list[OrderLine] = []
        self._status = "draft"

    def add_line(self, product: str, quantity: int, unit_price: Money) -> None:
        if self._status != "draft":
            raise ValueError("已送出的訂單不能加項目")  # 不變條件
        self._lines.append(OrderLine(product, quantity, unit_price))

    def total(self) -> Money:
        result = Money(Decimal(0))
        for line in self._lines:
            result = result + line.subtotal()
        return result

    def submit(self) -> None:
        if not self._lines:
            raise ValueError("空訂單不能送出")  # 不變條件
        self._status = "submitted"

    @property
    def status(self) -> str:
        return self._status


# ===== Hexagonal：ports & adapters（見 09）=====
@dataclass
class OrderRecord:
    id: int
    amount: int


class OrderStorePort(Protocol):
    def save(self, order: OrderRecord) -> None: ...
    def get(self, order_id: int) -> OrderRecord | None: ...


class NotificationPort(Protocol):
    def notify(self, message: str) -> None: ...


class PlaceOrderUseCase:
    """核心 use case：只依賴 ports，不知道具體技術。"""

    def __init__(self, store: OrderStorePort, notifier: NotificationPort) -> None:
        self._store = store
        self._notifier = notifier

    def execute(self, order: OrderRecord) -> None:
        self._store.save(order)
        self._notifier.notify(f"訂單 {order.id} 已成立（金額 {order.amount}）")


class InMemoryOrderStore:
    def __init__(self) -> None:
        self._orders: dict[int, OrderRecord] = {}

    def save(self, order: OrderRecord) -> None:
        self._orders[order.id] = order

    def get(self, order_id: int) -> OrderRecord | None:
        return self._orders.get(order_id)


class FakeNotificationAdapter:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def notify(self, message: str) -> None:
        self.messages.append(message)


# ===== 事件驅動：event bus + 冪等消費者（見 10）=====
@dataclass(frozen=True)
class OrderPlaced:
    event_id: str
    order_id: int
    amount: int


class EventBus:
    """簡易事件匯流排：發布訂閱（一對多）。此處針對 OrderPlaced 事件示範。"""

    def __init__(self) -> None:
        self._subscribers: list[Callable[[OrderPlaced], None]] = []

    def subscribe(self, handler: Callable[[OrderPlaced], None]) -> None:
        self._subscribers.append(handler)

    def publish(self, event: OrderPlaced) -> None:
        for handler in self._subscribers:
            handler(event)  # 同步模擬；真實為非同步 worker


class IdempotentEmailHandler:
    """冪等消費者：同一事件處理兩次也只寄一次（處理至少一次投遞造成的重複）。"""

    def __init__(self) -> None:
        self.sent: list[int] = []
        self._processed: set[str] = set()

    def handle(self, event: OrderPlaced) -> None:
        if event.event_id in self._processed:
            return  # 已處理過，去重（冪等）
        self._processed.add(event.event_id)
        self.sent.append(event.order_id)


# ===== 設定管理（見 11）=====
def to_bool(value: str) -> bool:
    """正確地把字串轉 bool——別用 bool(str)（非空字串永遠是 True）。"""
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str
    port: int
    debug: bool


def load_settings(env: dict[str, str]) -> Settings:
    """從環境字典載入設定：必填檢查 + 轉型 + 驗證（fail fast）。"""
    if "DATABASE_URL" not in env:
        raise ValueError("缺少必要設定 DATABASE_URL")
    try:
        port = int(env.get("PORT", "8000"))
    except ValueError:
        raise ValueError(f"PORT 必須是整數，得到 {env.get('PORT')!r}") from None
    if not (1 <= port <= 65535):
        raise ValueError(f"PORT 超出範圍：{port}")
    return Settings(
        database_url=env["DATABASE_URL"],
        port=port,
        debug=to_bool(env.get("DEBUG", "false")),
    )
