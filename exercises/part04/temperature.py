"""Part 4 練習:property 與封裝(承 05-encapsulation / 06-property)。

實作 Temperature:celsius(帶驗證,低於 -273.15 丟 ValueError)、
fahrenheit(讀取換算、設定時反算回 celsius)。
"""

from __future__ import annotations


class Temperature:
    """以攝氏為內部狀態,fahrenheit 為計算屬性。"""

    def __init__(self, celsius: float = 0.0) -> None:
        raise NotImplementedError("實作我!")

    @property
    def celsius(self) -> float:
        raise NotImplementedError("實作我!")

    @property
    def fahrenheit(self) -> float:
        raise NotImplementedError("實作我!")
