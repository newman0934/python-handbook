"""Part 4 練習:ABC 與多型(承 03-inheritance / 10-abc)。

實作 Shape(ABC,抽象 area)、Rectangle、Circle、total_area 讓測試轉綠。
Shape 不可被直接實例化。
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Shape(ABC):
    """抽象基底:所有形狀都要能算面積。"""

    @abstractmethod
    def area(self) -> float: ...


class Rectangle(Shape):
    def __init__(self, width: float, height: float) -> None:
        raise NotImplementedError("實作我!")

    def area(self) -> float:
        raise NotImplementedError("實作我!")


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        raise NotImplementedError("實作我!")

    def area(self) -> float:
        raise NotImplementedError("實作我!")


def total_area(shapes: list[Shape]) -> float:
    raise NotImplementedError("實作我!")
