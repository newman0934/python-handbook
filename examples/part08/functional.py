"""Part 8 函數式與裝飾器的可執行範例。

對應章節：chapters/08-functional-decorators/
"""

from __future__ import annotations

from collections.abc import Callable
from functools import cache, partial, reduce, singledispatch, total_ordering, wraps
from typing import Any


# --- 分派表（一等公民） ---
def make_calculator() -> dict[str, Callable[[float, float], float]]:
    return {
        "+": lambda a, b: a + b,
        "-": lambda a, b: a - b,
        "*": lambda a, b: a * b,
    }


# --- 高階函式：函式組合 ---
def compose(*funcs: Callable[[int], int]) -> Callable[[int], int]:
    def composed(x: int) -> int:
        for f in reversed(funcs):
            x = f(x)
        return x

    return composed


def merge_dicts(dicts: list[dict[str, int]]) -> dict[str, int]:
    """用 reduce 合併 dict。"""
    return reduce(lambda acc, d: {**acc, **d}, dicts, {})


# --- 裝飾器基礎 + wraps ---
def logged(func: Callable[..., Any]) -> Callable[..., Any]:
    calls: list[str] = []

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        calls.append(func.__name__)
        return func(*args, **kwargs)

    wrapper.calls = calls  # type: ignore[attr-defined]
    return wrapper


# --- 帶參數的裝飾器 ---
def repeat(n: int) -> Callable[[Callable[..., Any]], Callable[..., list[Any]]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., list[Any]]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> list[Any]:
            return [func(*args, **kwargs) for _ in range(n)]

        return wrapper

    return decorator


# --- lru_cache ---
@cache
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


# --- total_ordering ---
@total_ordering
class Version:
    def __init__(self, major: int, minor: int) -> None:
        self.major = major
        self.minor = minor

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor) == (other.major, other.minor)

    def __lt__(self, other: Version) -> bool:
        return (self.major, self.minor) < (other.major, other.minor)

    def __repr__(self) -> str:
        return f"v{self.major}.{self.minor}"


# --- singledispatch ---
@singledispatch
def to_json(arg: object) -> str:
    return f'"{arg}"'


@to_json.register
def _(arg: int) -> str:
    return str(arg)


@to_json.register(list)
def _(arg: list[object]) -> str:
    return "[" + ", ".join(to_json(x) for x in arg) + "]"


# --- partial ---
to_binary = partial(int, base=2)
to_hex = partial(int, base=16)


# --- 類別作為裝飾器（保存狀態） ---
class CallCounter:
    def __init__(self, func: Callable[..., Any]) -> None:
        wraps(func)(self)
        self.func = func
        self.count = 0

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.count += 1
        return self.func(*args, **kwargs)

    def reset(self) -> None:
        self.count = 0


@CallCounter
def ping() -> str:
    return "pong"


# --- 裝飾類別：註冊 ---
registry: dict[str, type] = {}


def register(cls: type) -> type:
    registry[cls.__name__] = cls
    return cls
