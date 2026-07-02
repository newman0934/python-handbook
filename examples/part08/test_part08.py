"""Part 8 範例的驗證測試。

執行：pytest examples/part08
"""

from examples.part08.functional import (
    Version,
    compose,
    fib,
    logged,
    make_calculator,
    merge_dicts,
    ping,
    register,
    registry,
    repeat,
    to_binary,
    to_hex,
    to_json,
)


def test_dispatch_table() -> None:
    ops = make_calculator()
    assert ops["+"](3, 4) == 7
    assert ops["*"](3, 4) == 12


def test_compose() -> None:
    pipeline = compose(lambda x: x + 1, lambda x: x * 2)  # double then +1
    assert pipeline(3) == 7


def test_reduce_merge_dicts() -> None:
    assert merge_dicts([{"a": 1}, {"b": 2}, {"c": 3}]) == {"a": 1, "b": 2, "c": 3}


def test_decorator_wraps_preserves_name() -> None:
    @logged
    def add(a: int, b: int) -> int:
        """加法。"""
        return a + b

    assert add.__name__ == "add"
    assert add.__doc__ == "加法。"
    assert add(2, 3) == 5
    assert add.calls == ["add"]  # type: ignore[attr-defined]


def test_decorator_with_args() -> None:
    @repeat(3)
    def dice() -> int:
        return 4

    assert dice() == [4, 4, 4]


def test_lru_cache_fib() -> None:
    assert fib(10) == 55
    assert fib(50) == 12586269025


def test_total_ordering() -> None:
    assert Version(1, 5) < Version(2, 0)
    assert Version(1, 5) >= Version(1, 5)  # 自動產生
    assert sorted([Version(2, 0), Version(1, 5), Version(1, 10)]) == [
        Version(1, 5),
        Version(1, 10),
        Version(2, 0),
    ]


def test_singledispatch() -> None:
    assert to_json(42) == "42"
    assert to_json("hi") == '"hi"'
    assert to_json([1, 2]) == "[1, 2]"


def test_partial() -> None:
    assert to_binary("1010") == 10
    assert to_hex("ff") == 255


def test_class_decorator_state() -> None:
    ping()
    ping()
    ping()
    assert ping.count == 3
    ping.reset()
    assert ping.count == 0


def test_decorate_class_registers() -> None:
    @register
    class Widget:
        pass

    assert "Widget" in registry
    assert registry["Widget"] is Widget
