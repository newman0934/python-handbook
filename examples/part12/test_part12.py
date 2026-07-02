"""Part 12 測試範例：展示 pytest 基礎、fixture、參數化、mock。

執行：pytest examples/part12
"""

from unittest.mock import Mock

import pytest

from examples.part12.app import (
    ShoppingCart,
    WeatherService,
    calculate_discount,
    to_grade,
)


# --- pytest 基礎：裸 assert、pytest.raises、approx ---
def test_calculate_discount_normal() -> None:
    assert calculate_discount(100, 20) == 80.0


def test_calculate_discount_invalid_raises() -> None:
    with pytest.raises(ValueError, match="折扣須在 0-100"):
        calculate_discount(100, 150)


def test_float_approx() -> None:
    assert calculate_discount(99.99, 10) == pytest.approx(89.99, abs=1e-2)


# --- 參數化：一個邏輯、多組資料 ---
@pytest.mark.parametrize(
    ("score", "expected"),
    [(95, "A"), (85, "B"), (75, "C"), (65, "D"), (55, "F"), (90, "A"), (60, "D")],
    ids=["A上界", "B", "C", "D", "F", "A邊界", "D邊界"],
)
def test_grade_boundaries(score: int, expected: str) -> None:
    assert to_grade(score) == expected


# --- fixture：用 conftest.py 的 fixture（不必 import） ---
def test_empty_cart(empty_cart: ShoppingCart) -> None:
    assert empty_cart.total() == 0.0


def test_cart_with_items(cart_with_items: ShoppingCart) -> None:
    assert cart_with_items.total() == 50.0


def test_add_to_cart(cart_with_items: ShoppingCart) -> None:
    cart_with_items.add("橘子", 25.0)
    assert cart_with_items.total() == 75.0


# --- 內建 fixture：tmp_path ---
def test_tmp_path(tmp_path: object) -> None:
    from pathlib import Path

    assert isinstance(tmp_path, Path)
    file = tmp_path / "data.txt"
    file.write_text("測試", encoding="utf-8")
    assert file.read_text(encoding="utf-8") == "測試"


# --- mock：隔離外部依賴 ---
def test_weather_with_mock() -> None:
    mock_api = Mock()
    mock_api.fetch.return_value = {"temp": 25}

    service = WeatherService(mock_api)
    assert service.get_temperature("Taipei") == 25
    mock_api.fetch.assert_called_once_with("Taipei")  # 驗證互動


def test_is_hot_with_mock() -> None:
    mock_api = Mock()
    mock_api.fetch.return_value = {"temp": 35}
    assert WeatherService(mock_api).is_hot("Taipei") is True


def test_mock_side_effect_raises() -> None:
    mock_api = Mock()
    mock_api.fetch.side_effect = ConnectionError("網路斷線")  # 模擬失敗
    service = WeatherService(mock_api)
    with pytest.raises(ConnectionError):
        service.get_temperature("Taipei")


# --- monkeypatch：暫時修改環境變數 ---
def test_monkeypatch_env(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    monkeypatch.setenv("APP_TEST_KEY", "value123")
    assert os.environ["APP_TEST_KEY"] == "value123"
    # 測試結束自動還原
