"""Part 22 consistent_hash 測試。"""

from __future__ import annotations

from solutions.part22.consistent_hash import ConsistentHashRing


def _ring() -> ConsistentHashRing:
    r = ConsistentHashRing()
    for node in ("A", "B", "C"):
        r.add_node(node)
    return r


def test_get_node_returns_valid_node() -> None:
    assert _ring().get_node("mykey") in {"A", "B", "C"}


def test_mapping_is_stable() -> None:
    ring = _ring()
    first = ring.get_node("user:123")
    assert ring.get_node("user:123") == first
    assert ring.get_node("user:123") == first


def test_empty_ring_returns_none() -> None:
    assert ConsistentHashRing().get_node("x") is None
