"""Part 12 測試的被測程式（含 doctest）。

對應章節：chapters/12-testing/
"""

from __future__ import annotations


def to_grade(score: int) -> str:
    """把分數轉成等第。

    >>> to_grade(95)
    'A'
    >>> to_grade(60)
    'D'
    >>> to_grade(0)
    'F'
    """
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def calculate_discount(price: float, discount_percent: float) -> float:
    """計算折扣後價格。

    >>> calculate_discount(100, 20)
    80.0
    >>> calculate_discount(100, 0)
    100.0
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError(f"折扣須在 0-100，得到 {discount_percent}")
    return round(price * (1 - discount_percent / 100), 2)


class ShoppingCart:
    """購物車（示範 fixture 測試對象）。"""

    def __init__(self) -> None:
        self.items: list[tuple[str, float]] = []

    def add(self, name: str, price: float) -> None:
        self.items.append((name, price))

    def total(self) -> float:
        return sum(price for _, price in self.items)


class WeatherService:
    """依賴外部 API 的服務（示範 mock 測試對象）。"""

    def __init__(self, api_client: object) -> None:
        self.api = api_client

    def get_temperature(self, city: str) -> int:
        data = self.api.fetch(city)  # type: ignore[attr-defined]
        return int(data["temp"])

    def is_hot(self, city: str) -> bool:
        return self.get_temperature(city) > 30
