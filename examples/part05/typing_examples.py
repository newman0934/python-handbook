"""Part 5 型別系統的可執行範例（PEP 695 新泛型語法，mypy strict 通過）。

對應章節：chapters/05-typing/
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from functools import wraps
from typing import Literal, Self, TypedDict, TypeGuard, overload

Grade = Literal["A", "B", "C", "D", "F"]


# --- 泛型函式：PEP 695 新語法，保留型別關聯 ---
def first[T](items: list[T]) -> T:
    return items[0]


def total[Num: (int, float)](nums: Iterable[Num]) -> Num:
    it = iter(nums)
    result = next(it)
    for n in it:
        result = result + n
    return result


# --- 泛型類別：PEP 695 ---
class Box[T]:
    def __init__(self, item: T) -> None:
        self._item = item

    def get(self) -> T:
        return self._item


# --- Optional / 型別窄化 ---
def safe_upper(text: str | None) -> str:
    if text is None:
        return ""
    return text.upper()


def classify(x: int | str | None) -> str:
    if x is None:
        return "空"
    if isinstance(x, int):
        return f"整數{x}"
    return f"字串{x}"


# --- TypedDict ---
class Student(TypedDict):
    name: str
    score: int


def to_grade(score: int) -> Grade:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def report(student: Student) -> str:
    return f"{student['name']}: {to_grade(student['score'])}"


# --- overload：輸入型別決定輸出型別 ---
@overload
def parse(value: str) -> str: ...
@overload
def parse(value: int) -> list[int]: ...
def parse(value: str | int) -> str | list[int]:
    if isinstance(value, str):
        return value.strip()
    return list(range(value))


# --- TypeGuard：自訂窄化 ---
def is_int_list(val: list[object]) -> TypeGuard[list[int]]:
    return all(isinstance(x, int) for x in val)


def sum_if_ints(items: list[object]) -> int:
    if is_int_list(items):
        return sum(items)
    return 0


# --- ParamSpec（PEP 695 的 [**P]）：裝飾器保留簽章 ---
def call_twice[**P, R](func: Callable[P, R]) -> Callable[P, list[R]]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[R]:
        return [func(*args, **kwargs), func(*args, **kwargs)]

    return wrapper


@call_twice
def add(a: int, b: int) -> int:
    return a + b


# --- Self：鏈式呼叫 ---
class FluentList:
    def __init__(self) -> None:
        self._items: list[int] = []

    def add(self, x: int) -> Self:
        self._items.append(x)
        return self

    def build(self) -> list[int]:
        return self._items
