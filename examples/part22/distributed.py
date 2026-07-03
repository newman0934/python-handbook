"""Part 22 分散式系統範例：CAP / Quorum / 分散式鎖(fencing) /
訊息佇列(partition·at-least-once) / 快取策略 / 冪等 / Saga / 分散式追蹤。

全部純 stdlib，封裝可驗證的確定性邏輯。
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field


# ===== CAP：分區下 CP vs AP（見 01）=====
class ReplicatedStore:
    def __init__(self, mode: str) -> None:
        self.mode = mode  # "CP" 或 "AP"
        self.n1 = 1
        self.n2 = 1
        self.partitioned = False

    def partition(self) -> None:
        self.partitioned = True

    def write(self, value: int) -> bool:
        """回傳寫入是否成功。"""
        if self.partitioned:
            if self.mode == "CP":
                return False  # 拒絕寫入，保一致犧牲可用
            self.n1 = value  # AP：接受但只更新 N1
            return True
        self.n1 = self.n2 = value
        return True


# ===== 一致性：Quorum（見 02）=====
@dataclass
class VersionedValue:
    value: int
    version: int


class QuorumStore:
    def __init__(self, n: int) -> None:
        self.replicas = [VersionedValue(0, 0) for _ in range(n)]
        self._version = 0

    def write(self, value: int, w: int) -> None:
        self._version += 1
        for i in range(w):
            self.replicas[i] = VersionedValue(value, self._version)

    def read(self, r: int) -> int:
        return max(self.replicas[:r], key=lambda v: v.version).value


def is_strongly_consistent(n: int, w: int, r: int) -> bool:
    return w + r > n


# ===== 分散式鎖：fencing token（見 03）=====
class LockService:
    def __init__(self) -> None:
        self._holder: str | None = None
        self._token = 0

    def acquire(self, client: str) -> int | None:
        if self._holder is not None:
            return None
        self._holder = client
        self._token += 1
        return self._token

    def expire(self) -> None:
        self._holder = None


class ProtectedResource:
    def __init__(self) -> None:
        self.max_token = 0
        self.data: list[str] = []

    def write(self, value: str, token: int) -> bool:
        if token < self.max_token:
            return False  # fencing：拒絕過期持有者
        self.max_token = token
        self.data.append(value)
        return True


# ===== 訊息佇列：partition 保序 + at-least-once（見 04）=====
def partition_for(key: str, num_partitions: int) -> int:
    return sum(key.encode()) % num_partitions


class Topic:
    def __init__(self, num_partitions: int) -> None:
        self.num_partitions = num_partitions
        self.partitions: dict[int, list[str]] = defaultdict(list)

    def produce(self, key: str, msg: str) -> int:
        p = partition_for(key, self.num_partitions)
        self.partitions[p].append(msg)
        return p


def assign_partitions(num_partitions: int, num_consumers: int) -> dict[int, int]:
    return {p: p % num_consumers for p in range(num_partitions)}


# ===== 快取：cache-aside（見 05）=====
class Database:
    def __init__(self) -> None:
        self.data = {"user:1": "alice"}
        self.query_count = 0

    def query(self, key: str) -> str | None:
        self.query_count += 1
        return self.data.get(key)

    def update(self, key: str, value: str) -> None:
        self.data[key] = value


class CacheAside:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.cache: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        if key in self.cache:
            return self.cache[key]
        value = self.db.query(key)
        if value is not None:
            self.cache[key] = value
        return value

    def update(self, key: str, value: str) -> None:
        self.db.update(key, value)  # 先更新 DB
        self.cache.pop(key, None)  # 後刪快取(失效)


# ===== 冪等：idempotency key（見 06）=====
@dataclass
class PaymentService:
    balance: int = 1000
    _processed: dict[str, dict[str, object]] = field(default_factory=dict)

    def charge(self, idempotency_key: str, amount: int) -> dict[str, object]:
        if idempotency_key in self._processed:
            return {**self._processed[idempotency_key], "replayed": True}
        if self.balance < amount:
            raise ValueError("餘額不足")
        self.balance -= amount
        result: dict[str, object] = {"charged": amount, "balance": self.balance}
        self._processed[idempotency_key] = result
        return {**result, "replayed": False}


# ===== Saga：orchestration + 補償（見 07）=====
@dataclass
class Step:
    name: str
    action: Callable[[], None]
    compensation: Callable[[], None]


class SagaOrchestrator:
    def run(self, steps: list[Step]) -> tuple[bool, list[str]]:
        completed: list[Step] = []
        log: list[str] = []
        current = ""
        try:
            for step in steps:
                current = step.name
                step.action()
                completed.append(step)
                log.append(f"do:{step.name}")
            return True, log
        except Exception:
            log.append(f"fail:{current}")
            for step in reversed(completed):
                step.compensation()
                log.append(f"compensate:{step.name}")
            return False, log


# ===== 分散式追蹤：span 樹（見 08）=====
@dataclass
class Span:
    span_id: str
    trace_id: str
    parent_id: str | None
    operation: str
    start_ms: float
    end_ms: float
    children: list[Span] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        return self.end_ms - self.start_ms


def build_tree(spans: list[Span]) -> Span:
    by_id = {s.span_id: s for s in spans}
    root: Span | None = None
    for span in spans:
        if span.parent_id is None:
            root = span
        else:
            by_id[span.parent_id].children.append(span)
    assert root is not None
    return root


def slowest_leaf(spans: list[Span]) -> Span:
    return max((s for s in spans if not s.children), key=lambda s: s.duration_ms)
