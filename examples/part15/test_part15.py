"""Part 15 範例的驗證測試。

執行：pytest examples/part15
"""

import pytest

from examples.part15.database import (
    CachingRepository,
    ConnectionPool,
    FakeCache,
    Migration,
    MigrationRunner,
    QueryCounter,
    UserWithOrders,
    count_by_name,
    create_users_db,
    find_adults,
    get_balance,
    load_eager,
    load_n_plus_1,
    setup_accounts,
    transfer,
)


# --- DB-API / sqlite3 參數化查詢 ---
def test_find_adults_parametrized() -> None:
    conn = create_users_db()
    assert find_adults(conn, 18) == ["Bob", "Alice", "Cara"]
    conn.close()


def test_sql_injection_treated_as_data() -> None:
    conn = create_users_db()
    evil = "'; DROP TABLE users; --"
    # 惡意字串被當純資料，找不到、也不會 DROP 表
    assert count_by_name(conn, evil) == 0
    # 表還在，資料完整
    assert find_adults(conn, 0) == ["Dave", "Bob", "Alice", "Cara"]
    conn.close()


# --- 交易原子性 ---
def test_transfer_commits_on_success() -> None:
    conn = setup_accounts()
    transfer(conn, 1, 2, 300)
    assert get_balance(conn, 1) == 700
    assert get_balance(conn, 2) == 800
    conn.close()


def test_transfer_rolls_back_on_failure() -> None:
    conn = setup_accounts()
    with pytest.raises(ValueError, match="餘額不足"):
        transfer(conn, 2, 1, 99999)
    # rollback 後餘額不變、總額守恆
    assert get_balance(conn, 1) == 1000
    assert get_balance(conn, 2) == 500
    conn.close()


# --- 連線池 ---
def test_pool_reuses_connections() -> None:
    pool = ConnectionPool(pool_size=2, max_overflow=1)
    for _ in range(5):
        pool.acquire()
        pool.release()  # 用完歸還
    assert pool.created == 1  # 5 次借還只建立 1 條（重用）


def test_pool_exhaustion_raises() -> None:
    pool = ConnectionPool(pool_size=2, max_overflow=1)  # 硬上限 3
    for _ in range(3):
        pool.acquire()  # 借滿不還
    with pytest.raises(TimeoutError, match="耗盡"):
        pool.acquire()


# --- cache-aside ---
def test_cache_hit_avoids_db() -> None:
    repo = CachingRepository(FakeCache(), {1: "Alice"})
    assert repo.get_user(1) == "Alice"  # miss → DB
    for _ in range(5):
        repo.get_user(1)  # hit → 不打 DB
    assert repo.db_queries == 1


def test_cache_invalidated_on_update() -> None:
    repo = CachingRepository(FakeCache(), {1: "Alice"})
    repo.get_user(1)  # 快取 Alice
    repo.update_user(1, "Alice2")  # 更新 DB + 刪快取
    assert repo.get_user(1) == "Alice2"  # 重建，讀到新值
    assert repo.db_queries == 2


def test_cache_miss_for_unknown_key() -> None:
    repo = CachingRepository(FakeCache(), {1: "Alice"})
    assert repo.get_user(999) is None


# --- N+1 vs eager loading ---
def test_n_plus_1_query_count() -> None:
    users = [UserWithOrders(i, f"u{i}", [10, 20]) for i in range(1, 101)]
    counter = QueryCounter()
    total = load_n_plus_1(counter, users)
    assert counter.count == 101  # 1 + 100
    assert total == 100 * 30


def test_eager_loading_query_count() -> None:
    users = [UserWithOrders(i, f"u{i}", [10, 20]) for i in range(1, 101)]
    counter = QueryCounter()
    total = load_eager(counter, users)
    assert counter.count == 2  # 1 + 1
    assert total == 100 * 30


# --- migration 版本鏈 ---
def test_migration_upgrade_and_downgrade() -> None:
    migrations = [
        Migration("001", None, lambda s: s.add("users"), lambda s: s.discard("users")),
        Migration("002", "001", lambda s: s.add("orders"), lambda s: s.discard("orders")),
        Migration("003", "002", lambda s: s.add("payments"), lambda s: s.discard("payments")),
    ]
    runner = MigrationRunner(migrations)

    runner.upgrade_to_head()
    assert runner.current == "003"
    assert runner.schema == {"users", "orders", "payments"}

    runner.downgrade_one()
    assert runner.current == "002"
    assert runner.schema == {"users", "orders"}
