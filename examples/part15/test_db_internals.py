"""Part 15 資料庫原理(理論 ch01-ch10)範例測試。"""

from __future__ import annotations

from typing import cast

import pytest

from examples.part15.db_internals import (
    FD,
    BufferPool,
    MiniDB,
    MVCCRow,
    Primary,
    Replica,
    ScanDecision,
    SortedIndex,
    Table,
    Workload,
    can_use_composite_index,
    has_deadlock,
    hash_join_cost,
    hash_shard,
    join_rel,
    merge_join_cost,
    nested_loop_cost,
    polyglot_ops_load,
    project_rel,
    recommend_db,
    rehash_cost,
    relation,
    scan_pages_for_column,
    select_rel,
    sql_gt,
    violates_2nf,
    violates_3nf,
    where_keep,
)

# ---- ch01 關聯代數 ----


def _users() -> set[tuple[tuple[str, object], ...]]:
    return relation(
        [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Cara", "age": 30},
        ]
    )


def test_project_deduplicates() -> None:
    # 兩個 30 歲 → 投影 age 後去重成一個
    ages = project_rel(_users(), ["age"])
    assert len(ages) == 2


def test_select_filters() -> None:
    over26 = select_rel(_users(), lambda d: cast("int", d["age"]) > 26)
    assert {dict(r)["name"] for r in over26} == {"Alice", "Cara"}


def test_join_is_product_plus_selection() -> None:
    orders = relation([{"oid": 100, "uid": 1}, {"oid": 101, "uid": 2}])
    joined = join_rel(_users(), orders, "id", "uid")
    assert len(joined) == 2  # 只有配對到的 uid=1,2


def test_join_no_match_empty() -> None:
    orders = relation([{"oid": 1, "uid": 99}])
    assert join_rel(_users(), orders, "id", "uid") == set()


# ---- ch02 NULL 三值邏輯 ----


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (30, 26, True),
        (20, 26, False),
        (None, 26, None),  # UNKNOWN
        (30, None, None),
    ],
)
def test_sql_gt_three_valued(a: int | None, b: int | None, expected: bool | None) -> None:
    assert sql_gt(a, b) is expected


@pytest.mark.parametrize(
    "result, kept",
    [
        (True, True),
        (False, False),
        (None, False),  # WHERE 丟掉 UNKNOWN
    ],
)
def test_where_keep_only_true(result: bool | None, kept: bool) -> None:
    assert where_keep(result) is kept


# ---- ch03 正規化 ----


def _bad_table() -> Table:
    return Table(
        columns=frozenset(
            {"order_id", "product_id", "qty", "product_name", "customer_id", "customer_city"}
        ),
        primary_key=frozenset({"order_id", "product_id"}),
        fds=[
            FD(frozenset({"order_id", "product_id"}), frozenset({"qty"})),
            FD(frozenset({"product_id"}), frozenset({"product_name"})),
            FD(frozenset({"order_id"}), frozenset({"customer_id"})),
            FD(frozenset({"customer_id"}), frozenset({"customer_city"})),
        ],
    )


def test_detects_2nf_violation() -> None:
    assert len(violates_2nf(_bad_table())) == 2  # product_name, customer_id


def test_detects_3nf_violation() -> None:
    assert len(violates_3nf(_bad_table())) == 1  # customer_city 遞移


def test_normalized_table_clean() -> None:
    good = Table(
        columns=frozenset({"order_id", "product_id", "qty"}),
        primary_key=frozenset({"order_id", "product_id"}),
        fds=[FD(frozenset({"order_id", "product_id"}), frozenset({"qty"}))],
    )
    assert violates_2nf(good) == [] and violates_3nf(good) == []


def test_single_key_no_2nf_check() -> None:
    t = Table(frozenset({"id", "a"}), frozenset({"id"}), [FD(frozenset({"id"}), frozenset({"a"}))])
    assert violates_2nf(t) == []


# ---- ch04 buffer pool + 儲存佈局 ----


def test_buffer_pool_lru_eviction() -> None:
    pool = BufferPool(capacity=3)
    for pid in [1, 2, 3, 1, 2, 3, 1, 4, 1, 2]:
        pool.read_page(pid)
    # 頁 4 進來淘汰頁 2,最後存取 2 又 miss
    assert pool.disk_reads == 5
    assert pool.hits == 5
    assert pool.hit_ratio == 0.5


def test_columnar_reads_fewer_pages() -> None:
    row = scan_pages_for_column(1_000_000, 10, 8, 8192, columnar=False)
    col = scan_pages_for_column(1_000_000, 10, 8, 8192, columnar=True)
    assert col < row
    assert row // col == 9


# ---- ch05 索引 + 最左前綴 ----


def test_index_point_and_range() -> None:
    idx = SortedIndex()
    idx.build([(a,) for a in [30, 25, 40, 22, 35, 28, 50, 18]])
    assert idx.point_lookup((35,)) is True
    assert idx.point_lookup((99,)) is False
    assert sorted(a[0] for a in idx.range_scan((25,), (40,))) == [25, 28, 30, 35, 40]


@pytest.mark.parametrize(
    "eq, usable, used",
    [
        ({"a", "b"}, True, ["a", "b"]),
        ({"b"}, False, []),  # 缺最左 a
        ({"a", "c"}, True, ["a"]),  # 中間 b 斷,c 用不到
        ({"a", "b", "c"}, True, ["a", "b", "c"]),
    ],
)
def test_leftmost_prefix(eq: set[str], usable: bool, used: list[str]) -> None:
    u, cols = can_use_composite_index(["a", "b", "c"], eq)
    assert u is usable
    assert cols == used


# ---- ch06 JOIN 成本 + 掃描決策 ----


def test_join_algorithm_costs() -> None:
    assert nested_loop_cost(1000, 100000, False) == 100_000_000
    assert nested_loop_cost(1000, 100000, True) == 17_000
    assert hash_join_cost(1000, 100000) == 101_000
    # 有索引的 nested loop 比無索引便宜好幾個數量級
    assert nested_loop_cost(1000, 100000, True) < hash_join_cost(1000, 100000)


def test_merge_presorted_cheaper() -> None:
    assert merge_join_cost(1000, 100000, True) < merge_join_cost(1000, 100000, False)


@pytest.mark.parametrize(
    "sel, choice",
    [
        (0.001, "Index Scan"),  # 高選擇性
        (0.05, "Index Scan"),
        (0.5, "Seq Scan"),  # 低選擇性 → 全表掃描
    ],
)
def test_optimizer_scan_choice(sel: float, choice: str) -> None:
    assert ScanDecision(1_000_000, sel).choose() == choice


# ---- ch07 MVCC + 死鎖 ----


def test_mvcc_snapshot_isolation() -> None:
    row = MVCCRow()
    row.write(100, txid=1)
    row.commit(1)
    row.write(50, txid=5)  # 未 commit
    # 舊快照讀不到未 commit 的 50
    assert row.read(snapshot_max_committed_tx=1) == 100
    row.commit(5)
    assert row.read(snapshot_max_committed_tx=5) == 50


def test_deadlock_detection() -> None:
    assert has_deadlock({1: 2, 2: 3}) is None  # 無環
    assert has_deadlock({1: 2, 2: 1}) == [1, 2]  # 有環


def test_deadlock_longer_cycle() -> None:
    assert has_deadlock({1: 2, 2: 3, 3: 1}) is not None


# ---- ch08 WAL 恢復 ----


def test_wal_recovers_committed_undoes_uncommitted() -> None:
    db = MiniDB()
    db.write(1, "A", 100)
    db.write(1, "B", 0)
    db.write(1, "A", 0)
    db.write(1, "B", 100)
    db.commit(1)
    db.write(2, "A", 999)  # T2 未 commit
    db.crash()
    assert db.data == {}  # 崩潰:buffer 全丟
    db.recover()
    # T1 已 commit → redo;T2 未 commit → 不套用
    assert db.data == {"A": 0, "B": 100}


def test_wal_log_written_before_apply() -> None:
    db = MiniDB()
    db.write(1, "X", 5)
    # 每次 write 都先產生一條 WAL 紀錄
    assert any(r.kind == "write" and r.key == "X" for r in db.wal)


# ---- ch09 分片 + 複製 ----


def test_hash_shard_stable_and_in_range() -> None:
    for key in ["user:1", "user:2", "user:3"]:
        s = hash_shard(key, 4)
        assert 0 <= s < 4
        assert hash_shard(key, 4) == s  # 穩定


def test_modulo_resharding_moves_most_keys() -> None:
    keys = [f"user:{i}" for i in range(10000)]
    moved = rehash_cost(keys, 4, 5)
    assert moved > 0.5  # 取模擴容搬移大半 key


def test_replication_lag_read_your_writes() -> None:
    primary = Primary()
    replica = Replica()
    pos = primary.write("profile", 100)
    assert replica.read("profile") is None  # 複本落後:讀不到
    replica.apply_up_to(primary, pos)
    assert replica.read("profile") == 100  # 追上後可讀


# ---- ch10 選型 ----


@pytest.mark.parametrize(
    "w, expected",
    [
        (Workload("relational", "oltp", True, False), "relational"),
        (Workload("document", "oltp", False, False), "document"),
        (Workload("keyvalue", "oltp", False, False), "keyvalue"),
        (Workload("timeseries", "oltp", False, True), "timeseries"),
        (Workload("relational", "oltp", False, False, relationship_heavy=True), "graph"),
        (Workload("relational", "olap", False, False), "olap-columnar"),
        (Workload("document", "semantic", False, False), "vector"),
        (Workload("keyvalue", "oltp", False, True), "wide-column"),  # 海量寫入先於 KV
    ],
)
def test_recommend_db(w: Workload, expected: str) -> None:
    assert recommend_db(w) == expected


def test_strong_consistency_stays_relational() -> None:
    # 即使是 document,強一致需求也回關聯式
    assert recommend_db(Workload("document", "oltp", True, False)) == "relational"


def test_polyglot_cost_grows() -> None:
    assert polyglot_ops_load(1) < polyglot_ops_load(3) < polyglot_ops_load(5)
    assert polyglot_ops_load(3) == 6
