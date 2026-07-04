"""Part 15 ch24 MySQL 專屬功能 範例測試。"""

from __future__ import annotations

import pytest

from examples.part15.mysql_features import (
    AutoIncrement,
    InnoDBTable,
    fits_in_utf8mb3,
)

# ---- InnoDB 聚簇索引:兩次查找 vs 覆蓋索引 ----


def test_secondary_index_needs_two_traversals() -> None:
    t = InnoDBTable()
    t.insert(1, {"email": "a@x.com", "name": "Alice"})
    row = t.find_by_email("a@x.com", covering=False)
    assert row == {"email": "a@x.com", "name": "Alice"}
    assert t.traversals == 2  # 次要索引 → 主鍵 → 聚簇索引(回表)


def test_covering_index_single_traversal() -> None:
    t = InnoDBTable()
    t.insert(1, {"email": "a@x.com", "name": "Alice"})
    result = t.find_by_email("a@x.com", covering=True)
    assert result == {"email": "a@x.com", "pk": 1}
    assert t.traversals == 1  # 免回表


def test_find_missing_email() -> None:
    t = InnoDBTable()
    assert t.find_by_email("nope@x.com", covering=False) is None


# ---- utf8mb4 陷阱 ----


@pytest.mark.parametrize(
    "text, fits",
    [
        ("hello", True),  # ASCII 1-byte
        ("台灣繁體", True),  # CJK 3-byte
        ("😀", False),  # emoji 4-byte
        ("emoji 😀", False),  # 含 4-byte
        ("𝕏", False),  # 罕見數學字元 4-byte
    ],
)
def test_fits_in_utf8mb3(text: str, fits: bool) -> None:
    assert fits_in_utf8mb3(text) is fits


def test_emoji_is_four_bytes() -> None:
    assert len("😀".encode()) == 4


# ---- AUTO_INCREMENT 跳號 ----


def test_auto_increment_gaps_after_rollback() -> None:
    ai = AutoIncrement()
    got = [ai.next_id(), ai.next_id()]  # 1, 2
    _ = ai.next_id()  # 3 → 假設 rollback
    got.append(ai.next_id())  # 4(不回收)
    assert got == [1, 2, 4]  # 中間的 3 成為間隙


def test_auto_increment_monotonic() -> None:
    ai = AutoIncrement()
    ids = [ai.next_id() for _ in range(5)]
    assert ids == sorted(ids)
    assert len(set(ids)) == 5  # 不重複
