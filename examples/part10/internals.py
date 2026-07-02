"""Part 10 CPython 內部與記憶體的可執行範例。

對應章節：chapters/10-cpython-internals/
"""

from __future__ import annotations

import dis
import gc
import io
import sys
import weakref
from collections.abc import Callable
from contextlib import redirect_stdout


# --- 一切皆物件：任何東西都有 id/type ---
def object_info(obj: object) -> tuple[str, bool]:
    """回傳 (型別名, 是否為 object 的實例)。"""
    return type(obj).__name__, isinstance(obj, object)


# --- 物件模型：is vs == ---
def is_vs_eq(a: object, b: object) -> tuple[bool, bool]:
    """回傳 (a == b, a is b)。"""
    return a == b, a is b


# --- 引用計數 ---
def ref_count(obj: object) -> int:
    """回傳引用計數（扣掉 getrefcount 傳參的 1）。"""
    return sys.getrefcount(obj) - 1


# --- 循環 GC ---
class Node:
    def __init__(self, name: str) -> None:
        self.name = name
        self.ref: Node | None = None


def collect_cycles() -> int:
    """建立循環引用後手動 GC，回傳回收的物件數（>0 表示循環被回收）。"""
    gc.collect()  # 先清乾淨

    def make_cycle() -> None:
        a = Node("A")
        b = Node("B")
        a.ref = b
        b.ref = a  # 循環

    for _ in range(50):
        make_cycle()
    return gc.collect()


# --- bytecode / dis ---
def add(a: int, b: int) -> int:
    return a + b


def disassemble(func: Callable[..., object]) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        dis.dis(func)
    return buf.getvalue()


# --- 小整數 interning ---
def small_int_cached(n: int) -> bool:
    """判斷整數 n 是否在小整數快取範圍（透過 is 比較兩個獨立產生的值）。"""
    x = int(str(n))
    y = int(str(n))
    return x is y


# --- weakref ---
class Data:
    def __init__(self, value: int) -> None:
        self.value = value


def weakref_dies_with_object() -> tuple[int, bool]:
    """弱引用不阻止回收：回傳 (存活時的值, 回收後 ref() 是否為 None)。"""
    obj = Data(42)
    ref = weakref.ref(obj)
    resolved = ref()
    alive_value = resolved.value if resolved is not None else -1
    del resolved  # 釋放這個臨時強引用
    del obj  # 唯一強引用消失 → 物件被回收
    return alive_value, ref() is None


def weak_cache_auto_removes() -> tuple[bool, bool]:
    """WeakValueDictionary：物件沒外部引用就自動移除。"""
    cache: weakref.WeakValueDictionary[str, Data] = weakref.WeakValueDictionary()
    obj = Data(100)
    cache["k"] = obj
    before = "k" in cache
    del obj
    after = "k" in cache
    return before, after
