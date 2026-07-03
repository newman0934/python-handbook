"""Part 22 範例的驗證測試。

執行：pytest examples/part22
"""

from __future__ import annotations

from examples.part22.distributed import (
    CacheAside,
    Database,
    LockService,
    PaymentService,
    ProtectedResource,
    QuorumStore,
    ReplicatedStore,
    SagaOrchestrator,
    Span,
    Step,
    Topic,
    assign_partitions,
    build_tree,
    is_strongly_consistent,
    partition_for,
    slowest_leaf,
)


# --- CAP：CP vs AP（見 01）---
def test_cap_cp_vs_ap() -> None:
    cp = ReplicatedStore("CP")
    cp.partition()
    assert cp.write(2) is False  # CP 分區時拒絕寫入（保一致）
    assert cp.n2 == 1  # N2 一致（沒讓不一致寫入成功）

    ap = ReplicatedStore("AP")
    ap.partition()
    assert ap.write(2) is True  # AP 分區時接受寫入（保可用）
    assert ap.n2 == 1  # 但 N2 讀到舊值（不一致）


# --- Quorum（見 02）---
def test_quorum_consistency() -> None:
    assert is_strongly_consistent(3, 2, 2) is True  # W+R=4>3
    assert is_strongly_consistent(3, 1, 1) is False  # W+R=2<=3

    strong = QuorumStore(3)
    strong.write(42, w=2)
    assert strong.read(r=2) == 42  # W+R>N → 讀到最新
    # 最終一致：問到落後節點讀到舊值
    eventual = QuorumStore(3)
    eventual.write(42, w=1)
    assert eventual.replicas[2].value == 0  # 副本 2 未更新


# --- 分散式鎖：fencing token（見 03）---
def test_fencing_token_blocks_stale_holder() -> None:
    lock = LockService()
    resource = ProtectedResource()
    token_a = lock.acquire("A")
    assert token_a == 1
    lock.expire()  # A 卡住，鎖過期
    token_b = lock.acquire("B")
    assert token_b == 2
    assert resource.write("B", token_b) is True
    # A 恢復，帶舊 token 來寫 → 被 fencing 擋下
    assert token_a is not None
    assert resource.write("A stale", token_a) is False
    assert resource.data == ["B"]


# --- 訊息佇列：partition 保序（見 04）---
def test_partition_ordering() -> None:
    topic = Topic(3)
    p1 = topic.produce("order-123", "created")
    p2 = topic.produce("order-123", "paid")
    assert p1 == p2  # 同 key 進同 partition（保序）
    assert topic.partitions[p1] == ["created", "paid"]


def test_partition_deterministic() -> None:
    assert partition_for("order-123", 3) == partition_for("order-123", 3)


def test_consumer_group_assignment() -> None:
    assert assign_partitions(3, 2) == {0: 0, 1: 1, 2: 0}


# --- 快取：cache-aside（見 05）---
def test_cache_aside_hit_and_invalidate() -> None:
    db = Database()
    cache = CacheAside(db)
    assert cache.get("user:1") == "alice"  # miss → 查 DB
    assert db.query_count == 1
    assert cache.get("user:1") == "alice"  # 命中快取
    assert db.query_count == 1  # 沒再查 DB
    # 更新 → 失效 → 下次讀最新
    cache.update("user:1", "alice_new")
    assert "user:1" not in cache.cache
    assert cache.get("user:1") == "alice_new"


# --- 冪等：idempotency key（見 06）---
def test_idempotency_key_no_double_charge() -> None:
    svc = PaymentService(balance=1000)
    key = "pay-1"
    r1 = svc.charge(key, 100)
    assert r1["replayed"] is False
    r2 = svc.charge(key, 100)  # 同 key 重試
    assert r2["replayed"] is True
    svc.charge(key, 100)  # 再重試
    assert svc.balance == 900  # 只扣一次
    # 不同 key 各自生效
    svc.charge("pay-2", 50)
    assert svc.balance == 850


# --- Saga：補償（見 07）---
def test_saga_success() -> None:
    state = {"n": 0}
    steps = [
        Step("a", lambda: state.__setitem__("n", state["n"] + 1), lambda: None),
        Step("b", lambda: state.__setitem__("n", state["n"] + 10), lambda: None),
    ]
    ok, log = SagaOrchestrator().run(steps)
    assert ok is True
    assert state["n"] == 11


def test_saga_failure_compensates_in_reverse() -> None:
    state = {"inventory": 10, "balance": 1000}

    def fail() -> None:
        raise RuntimeError("訂單服務不可用")

    steps = [
        Step(
            "扣庫存",
            lambda: state.__setitem__("inventory", state["inventory"] - 1),
            lambda: state.__setitem__("inventory", state["inventory"] + 1),
        ),
        Step(
            "扣款",
            lambda: state.__setitem__("balance", state["balance"] - 100),
            lambda: state.__setitem__("balance", state["balance"] + 100),
        ),
        Step("建訂單", fail, lambda: None),
    ]
    ok, log = SagaOrchestrator().run(steps)
    assert ok is False
    # 反序補償後回到原值
    assert state == {"inventory": 10, "balance": 1000}
    assert log == ["do:扣庫存", "do:扣款", "fail:建訂單", "compensate:扣款", "compensate:扣庫存"]


# --- 分散式追蹤：span 樹（見 08）---
def test_tracing_locate_bottleneck() -> None:
    tid = "t1"
    spans = [
        Span("s1", tid, None, "gateway", 0, 2000),
        Span("s2", tid, "s1", "order-service", 20, 1980),
        Span("s3", tid, "s2", "query-inventory", 30, 130),
        Span("s4", tid, "s2", "db-query", 350, 1950),
    ]
    root = build_tree(spans)
    assert root.operation == "gateway"
    assert root.duration_ms == 2000
    assert len(root.children) == 1  # order-service
    slow = slowest_leaf(spans)
    assert slow.operation == "db-query"  # 瓶頸
    assert slow.duration_ms == 1600
