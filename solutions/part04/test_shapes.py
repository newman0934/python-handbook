"""Part 4 shapes 測試。"""

from __future__ import annotations

import math

import pytest

from solutions.part04.shapes import Circle, Rectangle, Shape, total_area


def test_rectangle_area() -> None:
    assert Rectangle(3, 4).area() == 12


def test_circle_area() -> None:
    assert Circle(2).area() == pytest.approx(4 * math.pi)


def test_total_area() -> None:
    assert total_area([Rectangle(2, 3), Circle(1)]) == pytest.approx(6 + math.pi)


def test_cannot_instantiate_abstract() -> None:
    with pytest.raises(TypeError):
        Shape()  # type: ignore[abstract]
