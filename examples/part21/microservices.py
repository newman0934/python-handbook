"""Part 21 微服務範例：服務邊界 / 同步非同步通訊 / 服務發現 /
API gateway / 健康檢查 / 熔斷器 / 集中設定 + feature flag / protobuf 編碼。

全部純 stdlib，封裝可驗證的確定性邏輯。
"""

from __future__ import annotations

import json
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeVar

T = TypeVar("T")


# ===== 服務邊界：database-per-service（見 01）=====
class UserService:
    def __init__(self) -> None:
        self._users: dict[int, str] = {}

    def create_user(self, user_id: int, name: str) -> None:
        self._users[user_id] = name

    def get_user_name(self, user_id: int) -> str | None:
        return self._users.get(user_id)


@dataclass
class OrderService:
    users: UserService  # 依賴使用者服務的 API，不是它的資料庫
    _orders: dict[int, dict[str, object]] = field(default_factory=dict)
    _next_id: int = 1

    def place_order(self, user_id: int, amount: int) -> dict[str, object]:
        name = self.users.get_user_name(user_id)
        if name is None:
            raise ValueError(f"使用者 {user_id} 不存在")
        order = {"id": self._next_id, "user": name, "amount": amount}
        self._orders[self._next_id] = order
        self._next_id += 1
        return order


# ===== 非同步通訊：訊息佇列解耦（見 03）=====
class MessageBroker:
    def __init__(self) -> None:
        self.queue: deque[str] = deque()

    def publish(self, msg: str) -> None:
        self.queue.append(msg)

    def consume_all(self, handler: Callable[[str], bool]) -> int:
        """handler 回傳是否成功；失敗則訊息留在佇列（下游恢復後補處理）。"""
        processed = 0
        while self.queue:
            if not handler(self.queue[0]):
                break
            self.queue.popleft()
            processed += 1
        return processed


# ===== 服務發現：註冊中心 + 健康過濾 + round-robin（見 04）=====
@dataclass
class Instance:
    address: str
    healthy: bool = True
    last_heartbeat: float = 0.0


@dataclass
class ServiceRegistry:
    ttl: float = 10.0
    _services: dict[str, dict[str, Instance]] = field(default_factory=dict)

    def register(self, service: str, address: str, now: float) -> None:
        self._services.setdefault(service, {})[address] = Instance(address, True, now)

    def set_health(self, service: str, address: str, healthy: bool) -> None:
        inst = self._services.get(service, {}).get(address)
        if inst:
            inst.healthy = healthy

    def discover(self, service: str, now: float) -> list[str]:
        instances = self._services.get(service, {})
        return sorted(
            addr
            for addr, inst in instances.items()
            if inst.healthy and (now - inst.last_heartbeat) <= self.ttl
        )


class RoundRobinBalancer:
    def __init__(self) -> None:
        self._counter = 0

    def pick(self, instances: list[str]) -> str | None:
        if not instances:
            return None
        choice = instances[self._counter % len(instances)]
        self._counter += 1
        return choice


# ===== API gateway：認證 + 限流 + 路由（見 05）=====
@dataclass
class Gateway:
    routes: dict[str, str]
    valid_tokens: set[str]
    rate_limit: int
    _counts: dict[str, int] = field(default_factory=dict)

    def handle(self, path: str, token: str | None) -> tuple[int, str]:
        if token not in self.valid_tokens:
            return 401, "Unauthorized"
        count = self._counts.get(token, 0) + 1
        self._counts[token] = count
        if count > self.rate_limit:
            return 429, "Too Many Requests"
        for prefix, service in self.routes.items():
            if path.startswith(prefix):
                return 200, service
        return 404, "Not Found"


# ===== 健康檢查：liveness 淺 / readiness 深（見 06）=====
@dataclass
class HealthChecker:
    started: bool = False
    critical_deps: dict[str, Callable[[], bool]] = field(default_factory=dict)

    def liveness(self) -> bool:
        """存活：只檢查行程本身（不查外部依賴）。"""
        return True

    def readiness(self) -> bool:
        """就緒：啟動完成 + 所有關鍵依賴可用。"""
        return self.started and all(check() for check in self.critical_deps.values())


# ===== 熔斷器：三態狀態機（見 07）=====
class CircuitOpenError(RuntimeError):
    pass


class CircuitBreaker:
    def __init__(self, fail_threshold: int = 3, recovery_time: float = 5.0) -> None:
        self.fail_threshold = fail_threshold
        self.recovery_time = recovery_time
        self.state = "closed"
        self.failures = 0
        self.opened_at = 0.0

    def call(self, func: Callable[[], T], now: float) -> T:
        if self.state == "open":
            if now - self.opened_at >= self.recovery_time:
                self.state = "half-open"
            else:
                raise CircuitOpenError("熔斷開啟，快速失敗")
        try:
            result = func()
        except Exception:
            self.failures += 1
            if self.state == "half-open" or self.failures >= self.fail_threshold:
                self.state = "open"
                self.opened_at = now
            raise
        if self.state == "half-open":
            self.state = "closed"
        self.failures = 0
        return result


# ===== 服務治理：集中設定 + feature flag（見 08）=====
class ConfigCenter:
    def __init__(self) -> None:
        self._config: dict[str, object] = {}
        self._watchers: dict[str, list[Callable[[object], None]]] = {}

    def set(self, key: str, value: object) -> None:
        self._config[key] = value
        for callback in self._watchers.get(key, []):
            callback(value)

    def get(self, key: str, default: object = None) -> object:
        return self._config.get(key, default)

    def watch(self, key: str, callback: Callable[[object], None]) -> None:
        self._watchers.setdefault(key, []).append(callback)


@dataclass
class FeatureFlags:
    _flags: dict[str, int] = field(default_factory=dict)

    def set_rollout(self, flag: str, percent: int) -> None:
        self._flags[flag] = percent

    def is_enabled(self, flag: str, user_id: int) -> bool:
        return (user_id % 100) < self._flags.get(flag, 0)


# ===== protobuf 風格編碼：varint + 二進位（見 02）=====
def encode_varint(n: int) -> bytes:
    out = bytearray()
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def json_size(user_id: int, name: str, is_active: bool) -> int:
    return len(
        json.dumps(
            {"id": user_id, "name": name, "is_active": is_active}, separators=(",", ":")
        ).encode()
    )


def binary_size(user_id: int, name: str, is_active: bool) -> int:
    size = 1 + len(encode_varint(user_id))  # 欄位 1
    size += 1 + len(encode_varint(len(name.encode()))) + len(name.encode())  # 欄位 2
    size += 1 + 1  # 欄位 3 (bool)
    return size
