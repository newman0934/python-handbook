"""Part 12 共用 fixture（放 conftest.py 自動可用，不必 import）。"""

from __future__ import annotations

import pytest

from examples.part12.app import ShoppingCart


@pytest.fixture
def empty_cart() -> ShoppingCart:
    """提供空購物車。"""
    return ShoppingCart()


@pytest.fixture
def cart_with_items(empty_cart: ShoppingCart) -> ShoppingCart:
    """組合 fixture：在空車上加商品。"""
    empty_cart.add("蘋果", 30.0)
    empty_cart.add("香蕉", 20.0)
    return empty_cart
