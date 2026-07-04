"""Part 15 資料庫原理(理論 ch01-ch10)可執行範例。

用純標準庫模擬資料庫引擎的核心機制,全部可離線測試:

- ch01 關聯代數(select / project / join)
- ch02 SQL 邏輯處理順序 + NULL 三值邏輯
- ch03 正規化違規偵測(函數相依)
- ch04 buffer pool(LRU)+ 行式/欄式 I/O
- ch05 B+tree 式索引(排序 + 二分)+ 最左前綴
- ch06 JOIN 演算法成本 + 索引 vs 全表掃描
- ch07 MVCC 快照可見性 + 死鎖偵測
- ch08 WAL + 崩潰恢復(redo/undo)
- ch09 分片路由 + 複製延遲 + 取模擴容成本
- ch10 資料庫選型決策
"""

from __future__ import annotations

import bisect
import hashlib
import math
from collections import OrderedDict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any

Row = dict[str, Any]

# ---------------------------------------------------------------------------
# ch01 關聯代數
# ---------------------------------------------------------------------------

RelRow = tuple[tuple[str, object], ...]


def relation(rows: list[dict[str, object]]) -> set[RelRow]:
    return {tuple(sorted(r.items())) for r in rows}


def select_rel(rel: set[RelRow], pred: Callable[[dict[str, object]], bool]) -> set[RelRow]:
    return {r for r in rel if pred(dict(r))}


def project_rel(rel: set[RelRow], cols: list[str]) -> set[RelRow]:
    return {tuple(sorted((c, dict(r)[c]) for c in cols)) for r in rel}


def join_rel(a: set[RelRow], b: set[RelRow], left_key: str, right_key: str) -> set[RelRow]:
    out: set[RelRow] = set()
    for ra in a:
        da = dict(ra)
        for rb in b:
            db = dict(rb)
            if da[left_key] == db[right_key]:
                merged = {f"L.{k}": v for k, v in da.items()}
                merged.update({f"R.{k}": v for k, v in db.items()})
                out.add(tuple(sorted(merged.items())))
    return out


# ---------------------------------------------------------------------------
# ch02 SQL 邏輯處理順序 + NULL 三值邏輯
# ---------------------------------------------------------------------------


def sql_gt(a: Any, b: Any) -> bool | None:
    if a is None or b is None:
        return None
    return bool(a > b)


def where_keep(pred_result: bool | None) -> bool:
    """WHERE 只保留 TRUE;UNKNOWN(None)與 FALSE 都丟掉。"""
    return pred_result is True


# ---------------------------------------------------------------------------
# ch03 正規化違規偵測
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FD:
    lhs: frozenset[str]
    rhs: frozenset[str]


@dataclass
class Table:
    columns: frozenset[str]
    primary_key: frozenset[str]
    fds: list[FD]

    @property
    def non_key(self) -> frozenset[str]:
        return self.columns - self.primary_key


def violates_2nf(t: Table) -> list[str]:
    problems: list[str] = []
    if len(t.primary_key) < 2:
        return problems
    for r in range(1, len(t.primary_key)):
        for sub in combinations(t.primary_key, r):
            subset = frozenset(sub)
            for fd in t.fds:
                if fd.lhs == subset and (fd.rhs & t.non_key):
                    problems.append(f"2NF: {set(fd.rhs & t.non_key)} on {set(subset)}")
    return problems


def violates_3nf(t: Table) -> list[str]:
    problems: list[str] = []
    for fd in t.fds:
        if (
            not (fd.lhs & t.primary_key)
            and (fd.rhs & t.non_key)
            and fd.lhs <= t.columns
            and (fd.lhs & t.non_key)
        ):
            problems.append(f"3NF: {set(fd.rhs & t.non_key)} via {set(fd.lhs)}")
    return problems


# ---------------------------------------------------------------------------
# ch04 buffer pool + 行式/欄式 I/O
# ---------------------------------------------------------------------------


@dataclass
class BufferPool:
    capacity: int
    cache: OrderedDict[int, bool] = field(default_factory=OrderedDict)
    disk_reads: int = 0
    hits: int = 0

    def read_page(self, page_id: int) -> None:
        if page_id in self.cache:
            self.cache.move_to_end(page_id)
            self.hits += 1
            return
        self.disk_reads += 1
        self.cache[page_id] = True
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.disk_reads
        return round(self.hits / total, 3) if total else 0.0


def scan_pages_for_column(
    n_rows: int, cols_per_row: int, col_bytes: int, page_size: int, columnar: bool
) -> int:
    row_bytes = cols_per_row * col_bytes
    col_data = n_rows * col_bytes if columnar else n_rows * row_bytes
    return -(-col_data // page_size)


# ---------------------------------------------------------------------------
# ch05 B+tree 式索引 + 最左前綴
# ---------------------------------------------------------------------------


@dataclass
class SortedIndex:
    keys: list[tuple[Any, ...]] = field(default_factory=list)
    probes: int = 0

    def build(self, rows: list[tuple[Any, ...]]) -> None:
        self.keys = sorted(rows)

    def point_lookup(self, key: tuple[Any, ...]) -> bool:
        self.probes += 1
        i = bisect.bisect_left(self.keys, key)
        return i < len(self.keys) and self.keys[i] == key

    def range_scan(self, low: tuple[Any, ...], high: tuple[Any, ...]) -> list[tuple[Any, ...]]:
        self.probes += 1
        i = bisect.bisect_left(self.keys, low)
        out: list[tuple[Any, ...]] = []
        while i < len(self.keys) and self.keys[i] <= high:
            out.append(self.keys[i])
            i += 1
        return out


def can_use_composite_index(
    index_cols: list[str], equality_cols: set[str]
) -> tuple[bool, list[str]]:
    used: list[str] = []
    for col in index_cols:
        if col in equality_cols:
            used.append(col)
        else:
            break
    return (len(used) > 0), used


# ---------------------------------------------------------------------------
# ch06 JOIN 演算法成本 + 掃描決策
# ---------------------------------------------------------------------------


def nested_loop_cost(outer_rows: int, inner_rows: int, inner_indexed: bool) -> int:
    per_probe = math.ceil(math.log2(inner_rows)) if inner_indexed else inner_rows
    return outer_rows * per_probe


def hash_join_cost(rows_a: int, rows_b: int) -> int:
    return rows_a + rows_b


def merge_join_cost(rows_a: int, rows_b: int, presorted: bool) -> int:
    if presorted:
        return rows_a + rows_b
    return rows_a * math.ceil(math.log2(rows_a)) + rows_b * math.ceil(math.log2(rows_b))


@dataclass
class ScanDecision:
    table_rows: int
    selectivity: float
    random_io_penalty: int = 4

    def index_scan_cost(self) -> int:
        return math.ceil(self.table_rows * self.selectivity * self.random_io_penalty)

    def seq_scan_cost(self) -> int:
        return self.table_rows

    def choose(self) -> str:
        return "Index Scan" if self.index_scan_cost() < self.seq_scan_cost() else "Seq Scan"


# ---------------------------------------------------------------------------
# ch07 MVCC + 死鎖偵測
# ---------------------------------------------------------------------------


@dataclass
class Version:
    value: int
    xmin: int
    committed: bool


@dataclass
class MVCCRow:
    versions: list[Version] = field(default_factory=list)

    def write(self, value: int, txid: int) -> None:
        self.versions.append(Version(value, txid, committed=False))

    def commit(self, txid: int) -> None:
        for v in self.versions:
            if v.xmin == txid:
                v.committed = True

    def read(self, snapshot_max_committed_tx: int) -> int | None:
        visible = [v for v in self.versions if v.committed and v.xmin <= snapshot_max_committed_tx]
        return visible[-1].value if visible else None


def has_deadlock(wait_for: dict[int, int]) -> list[int] | None:
    for start in wait_for:
        seen: list[int] = []
        cur: int | None = start
        while cur is not None and cur in wait_for:
            if cur in seen:
                return seen[seen.index(cur) :]
            seen.append(cur)
            cur = wait_for.get(cur)
    return None


# ---------------------------------------------------------------------------
# ch08 WAL + 崩潰恢復
# ---------------------------------------------------------------------------


@dataclass
class LogRecord:
    txid: int
    key: str
    old: int | None
    new: int | None
    kind: str


@dataclass
class MiniDB:
    data: dict[str, int] = field(default_factory=dict)
    wal: list[LogRecord] = field(default_factory=list)
    buffer: dict[str, int] = field(default_factory=dict)

    def write(self, txid: int, key: str, value: int) -> None:
        old = self.buffer.get(key, self.data.get(key))
        self.wal.append(LogRecord(txid, key, old, value, "write"))
        self.buffer[key] = value

    def commit(self, txid: int) -> None:
        self.wal.append(LogRecord(txid, "", None, None, "commit"))

    def crash(self) -> None:
        self.buffer.clear()

    def recover(self) -> None:
        committed = {r.txid for r in self.wal if r.kind == "commit"}
        for r in self.wal:
            if r.kind == "write" and r.txid in committed and r.new is not None:
                self.data[r.key] = r.new


# ---------------------------------------------------------------------------
# ch09 分片 + 複製延遲
# ---------------------------------------------------------------------------


def hash_shard(key: str, n: int) -> int:
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    return h % n


def rehash_cost(keys: list[str], old_n: int, new_n: int) -> float:
    moved = sum(1 for k in keys if hash_shard(k, old_n) != hash_shard(k, new_n))
    return round(moved / len(keys), 3)


@dataclass
class Primary:
    data: dict[str, int] = field(default_factory=dict)
    log_position: int = 0

    def write(self, key: str, value: int) -> int:
        self.data[key] = value
        self.log_position += 1
        return self.log_position


@dataclass
class Replica:
    data: dict[str, int] = field(default_factory=dict)
    applied_position: int = 0

    def apply_up_to(self, primary: Primary, position: int) -> None:
        self.data = dict(primary.data)
        self.applied_position = position

    def read(self, key: str) -> int | None:
        return self.data.get(key)


# ---------------------------------------------------------------------------
# ch10 資料庫選型
# ---------------------------------------------------------------------------


@dataclass
class Workload:
    data_model: str
    access: str
    strong_consistency: bool
    huge_write_scale: bool
    relationship_heavy: bool = False


def recommend_db(w: Workload) -> str:
    if w.access == "olap":
        return "olap-columnar"
    if w.access == "semantic":
        return "vector"
    if w.access == "search":
        return "search"
    if w.relationship_heavy or w.data_model == "graph":
        return "graph"
    if w.data_model == "timeseries":
        return "timeseries"
    if w.huge_write_scale and not w.strong_consistency:
        return "wide-column"
    if w.data_model == "keyvalue":
        return "keyvalue"
    if w.data_model == "document" and not w.strong_consistency:
        return "document"
    return "relational"


def polyglot_ops_load(db_count: int) -> int:
    return db_count * (db_count + 1) // 2


# ---------------------------------------------------------------------------


def query(rows: Iterable[Row], *, where: Callable[[Row], bool | None] | None = None) -> list[Row]:
    """簡化查詢:僅示範 WHERE 的三值邏輯過濾(FROM→WHERE)。"""
    data = list(rows)
    if where:
        data = [r for r in data if where_keep(where(r))]
    return data


def main() -> None:  # pragma: no cover
    print("ch01 join:", len(join_rel(relation([{"id": 1}]), relation([{"uid": 1}]), "id", "uid")))
    print("ch06 seq vs idx:", ScanDecision(1_000_000, 0.5).choose())
    print("ch09 rehash 4->5:", rehash_cost([f"u{i}" for i in range(1000)], 4, 5))
    print("ch10 金流:", recommend_db(Workload("relational", "oltp", True, False)))


if __name__ == "__main__":
    main()
