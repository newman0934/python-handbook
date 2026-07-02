"""Part 15 資料庫範例：用內建 sqlite3 與純邏輯模擬，不需外部服務即可測試。

涵蓋：DB-API 參數化查詢（防 injection）、交易原子性、連線池借還、
cache-aside 快取、N+1 vs eager loading、migration 版本鏈。
"""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass, field


# --- DB-API / sqlite3：參數化查詢（見 01, 02）---
def create_users_db() -> sqlite3.Connection:
    """建立記憶體資料庫並填入測試資料。"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, age INTEGER)")
    conn.executemany(
        "INSERT INTO users (name, age) VALUES (?, ?)",
        [("Alice", 30), ("Bob", 25), ("Cara", 35), ("Dave", 17)],
    )
    conn.commit()
    return conn


def find_adults(conn: sqlite3.Connection, min_age: int) -> list[str]:
    """參數化查詢（防 SQL injection）。"""
    cur = conn.execute(
        "SELECT name FROM users WHERE age >= ? ORDER BY age",
        (min_age,),
    )
    return [row["name"] for row in cur]


def count_by_name(conn: sqlite3.Connection, name: str) -> int:
    """惡意輸入被當純資料，不會執行 SQL injection。"""
    cur = conn.execute("SELECT COUNT(*) AS c FROM users WHERE name = ?", (name,))
    return int(cur.fetchone()["c"])


# --- 交易原子性（見 06）---
def setup_accounts() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE accounts (id INTEGER PRIMARY KEY, name TEXT, balance INTEGER)")
    conn.executemany(
        "INSERT INTO accounts VALUES (?, ?, ?)",
        [(1, "Alice", 1000), (2, "Bob", 500)],
    )
    conn.commit()
    return conn


def transfer(conn: sqlite3.Connection, from_id: int, to_id: int, amount: int) -> None:
    """原子轉帳：全成功或全撤銷。"""
    try:
        row = conn.execute("SELECT balance FROM accounts WHERE id = ?", (from_id,)).fetchone()
        if row[0] < amount:
            raise ValueError("餘額不足")
        conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, from_id))
        conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, to_id))
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def get_balance(conn: sqlite3.Connection, account_id: int) -> int:
    row = conn.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,)).fetchone()
    return int(row[0])


# --- 連線池借還（見 05）---
class ConnectionPool:
    """模擬連線池的借還與上限。"""

    def __init__(self, pool_size: int, max_overflow: int) -> None:
        self.hard_limit = pool_size + max_overflow
        self.checked_out = 0
        self.created = 0

    def acquire(self) -> str:
        if self.checked_out >= self.hard_limit:
            raise TimeoutError(f"連線池耗盡（上限 {self.hard_limit}）")
        self.checked_out += 1
        if self.checked_out > self.created:
            self.created += 1
        return f"連線#{self.checked_out}"

    def release(self) -> None:
        if self.checked_out > 0:
            self.checked_out -= 1


# --- cache-aside 快取（見 08）---
class FakeCache:
    """模擬帶 TTL 的記憶體快取。"""

    def __init__(self) -> None:
        self.store: dict[str, tuple[str, float | None]] = {}

    def get(self, key: str) -> str | None:
        if key not in self.store:
            return None
        value, expire_at = self.store[key]
        if expire_at is not None and time.monotonic() > expire_at:
            del self.store[key]
            return None
        return value

    def set(self, key: str, value: str, ex: float | None = None) -> None:
        expire_at = time.monotonic() + ex if ex is not None else None
        self.store[key] = (value, expire_at)

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


@dataclass
class CachingRepository:
    """cache-aside：讀先查快取、miss 查 DB 寫回、寫時刪快取。"""

    cache: FakeCache
    data: dict[int, str]
    db_queries: int = 0

    def get_user(self, user_id: int) -> str | None:
        key = f"user:{user_id}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        self.db_queries += 1  # 只有 miss 才打 DB
        user = self.data.get(user_id)
        if user is not None:
            self.cache.set(key, user, ex=300)
        return user

    def update_user(self, user_id: int, name: str) -> None:
        self.data[user_id] = name
        self.cache.delete(f"user:{user_id}")  # 刪快取，下次讀重建


# --- N+1 vs eager loading（見 10）---
@dataclass
class QueryCounter:
    count: int = 0

    def query(self) -> None:
        self.count += 1


@dataclass
class UserWithOrders:
    id: int
    name: str
    order_amounts: list[int] = field(default_factory=list)


def load_n_plus_1(counter: QueryCounter, users: list[UserWithOrders]) -> int:
    """lazy loading：迴圈存取關聯 → 1 + N 次查詢。"""
    counter.query()  # 查 users
    total = 0
    for user in users:
        counter.query()  # 每個 user 各查一次 orders
        total += sum(user.order_amounts)
    return total


def load_eager(counter: QueryCounter, users: list[UserWithOrders]) -> int:
    """eager loading：1 次查 users + 1 次查所有 orders。"""
    counter.query()  # 查 users
    counter.query()  # 一次 IN 查所有 orders
    return sum(sum(u.order_amounts) for u in users)


# --- migration 版本鏈（見 07）---
@dataclass
class Migration:
    revision: str
    down_revision: str | None
    upgrade: Callable[[set[str]], None]
    downgrade: Callable[[set[str]], None]


@dataclass
class MigrationRunner:
    migrations: list[Migration]
    schema: set[str] = field(default_factory=set)
    current: str | None = None

    def upgrade_to_head(self) -> None:
        for m in self.migrations:
            if self.current is None or self._is_after(m.revision, self.current):
                m.upgrade(self.schema)
                self.current = m.revision

    def downgrade_one(self) -> None:
        m = next(m for m in self.migrations if m.revision == self.current)
        m.downgrade(self.schema)
        self.current = m.down_revision

    def _is_after(self, rev: str, current: str) -> bool:
        order = [m.revision for m in self.migrations]
        return order.index(rev) > order.index(current)
