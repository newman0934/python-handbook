"""Part 7 範例的驗證測試。

執行：pytest examples/part07
"""

from examples.part07.iterators import (
    Fibonacci,
    chain_all,
    flatten,
    group_by_first_letter,
    naturals,
    pipeline,
    read_in_chunks,
    running_average,
    take,
)


def test_iterable_is_repeatable() -> None:
    fib = Fibonacci(8)
    # 可重複遍歷（__iter__ 每次回新生成器）
    assert list(fib) == [0, 1, 1, 2, 3, 5, 8, 13]
    assert list(fib) == [0, 1, 1, 2, 3, 5, 8, 13]


def test_generator_is_one_shot() -> None:
    gen = (x for x in range(3))
    assert list(gen) == [0, 1, 2]
    assert list(gen) == []  # 耗盡


def test_read_in_chunks() -> None:
    assert list(read_in_chunks("abcdefg", 3)) == ["abc", "def", "g"]


def test_flatten_recursive() -> None:
    assert list(flatten([1, [2, [3, 4], 5], [6]])) == [1, 2, 3, 4, 5, 6]


def test_chain_all() -> None:
    assert list(chain_all([1, 2], (3, 4), range(5, 7))) == [1, 2, 3, 4, 5, 6]


def test_lazy_pipeline() -> None:
    data = "a,1,x\nb,2\nc,3,z\nbad\nd,4,w"
    assert pipeline(data) == [["a", "1", "x"], ["c", "3", "z"], ["d", "4", "w"]]


def test_take_from_infinite() -> None:
    assert take(naturals(), 5) == [0, 1, 2, 3, 4]


def test_groupby_needs_sort() -> None:
    assert group_by_first_letter(["apple", "banana", "avocado", "cherry"]) == {
        "a": ["apple", "avocado"],
        "b": ["banana"],
        "c": ["cherry"],
    }


def test_coroutine_running_average() -> None:
    avg = running_average()
    next(avg)  # priming
    assert avg.send(10) == 10.0
    assert avg.send(20) == 15.0
    assert avg.send(30) == 20.0
