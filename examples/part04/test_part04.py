"""Part 4 範例的驗證測試。

執行：pytest examples/part04
"""

import pytest

from examples.part04.oop import (
    Admin,
    Circle,
    Counter,
    Money,
    Priority,
    Product,
    Report,
    Service,
    Square,
    Stack,
    Status,
    Team,
    Temperature,
    total_area,
)


def test_class_attr_shared_instance_attr_independent() -> None:
    Counter.total_created = 0
    a = Counter("A")
    b = Counter("B")
    a.increment()
    a.increment()
    b.increment()
    assert a.count == 2
    assert b.count == 1
    assert Counter.total_created == 2


def test_property_setter_validation() -> None:
    t = Temperature(25)
    assert t.fahrenheit == 77.0
    t.celsius = 100
    assert t.fahrenheit == 212.0
    with pytest.raises(ValueError):
        t.celsius = -300


def test_cached_property_computes_once() -> None:
    r = Report([1, 2, 3])
    assert r.total == 6
    assert r.total == 6
    assert r.calls == 1  # 只計算一次


def test_classmethod_cls_polymorphism() -> None:
    a = Admin.from_email("bob@corp.com")
    assert isinstance(a, Admin)  # cls 綁定為 Admin，不是 User
    assert a.name == "bob"


def test_money_dunder() -> None:
    assert Money(150) + Money(250) == Money(400)
    assert sorted([Money(250), Money(150)]) == [Money(150), Money(250)]
    assert len({Money(150), Money(150)}) == 1  # frozen → hashable → 去重


def test_abc_polymorphism() -> None:
    shapes = [Circle(1), Square(2)]
    assert total_area(shapes) == pytest.approx(3.14159 + 4)


def test_abc_cannot_instantiate() -> None:
    from examples.part04.oop import Shape

    with pytest.raises(TypeError):
        Shape()  # type: ignore[abstract]


def test_mro_cooperative_super_runs_base_once() -> None:
    s = Service()
    # Base 只出現一次，順序符合協作式 super
    assert s.log == ["Base", "Timer", "Logger", "Service"]
    assert [c.__name__ for c in Service.__mro__] == [
        "Service",
        "LoggerMixin",
        "TimerMixin",
        "Base",
        "object",
    ]


def test_enum_singleton_and_reverse_lookup() -> None:
    assert Status.ACTIVE is Status["ACTIVE"]
    assert [s.name for s in Status] == ["PENDING", "ACTIVE", "CLOSED"]
    assert Priority.HIGH > Priority.LOW
    assert int(Priority.HIGH) == 10  # IntEnum 成員「是」int


def test_stack_composition_encapsulates() -> None:
    s = Stack()
    s.push(1)
    s.push(2)
    assert s.pop() == 2
    assert len(s) == 1
    assert not hasattr(s, "insert")  # 沒洩漏 list 的方法


def test_descriptor_reuse_validation() -> None:
    p = Product(100, 5)
    assert p.price == 100
    with pytest.raises(ValueError):
        p.quantity = -1


def test_dataclass_default_factory_independent() -> None:
    a = Team("A")
    b = Team("B")
    a.members.append("Alice")
    assert a.members == ["Alice"]
    assert b.members == []
