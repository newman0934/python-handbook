"""Part 10 範例的驗證測試。

執行：pytest examples/part10
"""

import pytest

from examples.part10.internals import (
    add,
    collect_cycles,
    disassemble,
    is_vs_eq,
    object_info,
    ref_count,
    small_int_cached,
    weak_cache_auto_removes,
    weakref_dies_with_object,
)


@pytest.mark.parametrize(
    ("obj", "expected_type"),
    [(42, "int"), ("hi", "str"), ([1], "list"), (int, "type")],
)
def test_everything_is_object(obj: object, expected_type: str) -> None:
    type_name, is_object = object_info(obj)
    assert type_name == expected_type
    assert is_object is True  # 一切都是 object 的實例


def test_is_vs_eq() -> None:
    a = [1, 2, 3]
    b = [1, 2, 3]
    eq, is_ = is_vs_eq(a, b)
    assert eq is True  # 值相等
    assert is_ is False  # 不是同一物件

    c = a
    eq2, is_2 = is_vs_eq(a, c)
    assert eq2 is True
    assert is_2 is True  # 別名，同一物件


def test_ref_count_increases() -> None:
    # 絕對值受函式呼叫層的臨時引用影響，故檢查「多一個引用時計數 +1」
    a = [1, 2, 3]
    before = ref_count(a)
    b = a  # noqa: F841
    after = ref_count(a)
    assert after == before + 1


def test_gc_collects_cycles() -> None:
    collected = collect_cycles()
    assert collected > 0  # 循環垃圾被回收（引用計數無法回收的）


def test_bytecode_disassembly() -> None:
    output = disassemble(add)
    # add 的 bytecode 應含載入變數與回傳
    assert "LOAD_FAST" in output
    assert "RETURN_VALUE" in output


def test_small_int_interning() -> None:
    # -5 到 256 在快取範圍
    assert small_int_cached(0) is True
    assert small_int_cached(256) is True
    # 超出範圍不保證（但 257 通常不快取）
    assert small_int_cached(257) is False


def test_weakref_does_not_prevent_gc() -> None:
    alive_value, dead = weakref_dies_with_object()
    assert alive_value == 42
    assert dead is True  # 物件回收後弱引用失效


def test_weak_value_dict_auto_removes() -> None:
    before, after = weak_cache_auto_removes()
    assert before is True  # 有強引用時在快取
    assert after is False  # 無強引用後自動移除
