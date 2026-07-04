"""Part 4 練習:ABC 與多型(承 03-inheritance / 10-abc)。"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod


class Shape(ABC):
    """抽象基底:所有形狀都要能算面積。"""

    @abstractmethod
    def area(self) -> float: ...


class Rectangle(Shape):
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius**2


def total_area(shapes: list[Shape]) -> float:
    return sum(s.area() for s in shapes)
