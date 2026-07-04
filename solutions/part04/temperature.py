"""Part 4 練習:property 與封裝(承 05-encapsulation / 06-property)。"""

from __future__ import annotations


class Temperature:
    """以攝氏為內部狀態,fahrenheit 為計算屬性。"""

    def __init__(self, celsius: float = 0.0) -> None:
        self._celsius = 0.0
        self.celsius = celsius  # 走 setter 做驗證

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("低於絕對零度")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        return self._celsius * 9 / 5 + 32

    @fahrenheit.setter
    def fahrenheit(self, value: float) -> None:
        self.celsius = (value - 32) * 5 / 9
