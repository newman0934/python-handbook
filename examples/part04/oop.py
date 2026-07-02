"""Part 4 物件導向的可執行範例。

對應章節：chapters/04-oop/
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto, unique
from functools import cached_property
from typing import cast


# --- class 屬性 vs instance 屬性 ---
class Counter:
    total_created = 0

    def __init__(self, name: str) -> None:
        self.name = name
        self.count = 0
        Counter.total_created += 1

    def increment(self) -> int:
        self.count += 1
        return self.count


# --- property + cached_property ---
class Temperature:
    def __init__(self, celsius: float) -> None:
        self.celsius = celsius

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


class Report:
    def __init__(self, numbers: list[int]) -> None:
        self.numbers = numbers
        self.calls = 0

    @cached_property
    def total(self) -> int:
        self.calls += 1
        return sum(self.numbers)


# --- classmethod 替代建構子 + cls 多型 ---
class User:
    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email = email

    @classmethod
    def from_email(cls, email: str) -> User:
        return cls(email.split("@")[0], email)


class Admin(User):
    pass


# --- dunder ---
@dataclass(frozen=True, order=True)
class Money:
    cents: int

    def __add__(self, other: Money) -> Money:
        return Money(self.cents + other.cents)


# --- ABC 多型 ---
class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...


class Circle(Shape):
    def __init__(self, r: float) -> None:
        self.r = r

    def area(self) -> float:
        return 3.14159 * self.r * self.r


class Square(Shape):
    def __init__(self, side: float) -> None:
        self.side = side

    def area(self) -> float:
        return self.side * self.side


def total_area(shapes: list[Shape]) -> float:
    return sum(s.area() for s in shapes)


# --- MRO 協作式 super ---
class Base:
    def __init__(self) -> None:
        self.log: list[str] = []
        self.log.append("Base")


class LoggerMixin(Base):
    def __init__(self) -> None:
        super().__init__()
        self.log.append("Logger")


class TimerMixin(Base):
    def __init__(self) -> None:
        super().__init__()
        self.log.append("Timer")


class Service(LoggerMixin, TimerMixin):
    def __init__(self) -> None:
        super().__init__()
        self.log.append("Service")


# --- Enum ---
@unique
class Status(Enum):
    PENDING = auto()
    ACTIVE = auto()
    CLOSED = auto()


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 5
    HIGH = 10


# --- 組合優於繼承：Stack 封裝良好 ---
class Stack:
    def __init__(self) -> None:
        self._items: list[object] = []

    def push(self, item: object) -> None:
        self._items.append(item)

    def pop(self) -> object:
        return self._items.pop()

    def __len__(self) -> int:
        return len(self._items)


# --- 描述器：可重用驗證 ---
class Positive:
    def __set_name__(self, owner: type, name: str) -> None:
        self._name = f"_{name}"

    def __get__(self, obj: object, objtype: type | None = None) -> float:
        return cast(float, getattr(obj, self._name))

    def __set__(self, obj: object, value: float) -> None:
        if value <= 0:
            raise ValueError(f"{self._name[1:]} 必須為正")
        setattr(obj, self._name, value)


class Product:
    price = Positive()
    quantity = Positive()

    def __init__(self, price: float, quantity: float) -> None:
        self.price = price
        self.quantity = quantity


# --- mutable class attribute 陷阱示範（正解版） ---
@dataclass
class Team:
    name: str
    members: list[str] = field(default_factory=list)
