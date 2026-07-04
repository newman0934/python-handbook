"""Part 1 fizzbuzz 測試。"""

from __future__ import annotations

from exercises.part01.fizzbuzz import fizzbuzz


def test_basic_sequence() -> None:
    assert fizzbuzz(5) == ["1", "2", "Fizz", "4", "Buzz"]


def test_fizz_buzz_fizzbuzz() -> None:
    seq = fizzbuzz(15)
    assert seq[2] == "Fizz"
    assert seq[4] == "Buzz"
    assert seq[-1] == "FizzBuzz"


def test_length_matches_n() -> None:
    assert len(fizzbuzz(100)) == 100


def test_zero_or_negative_empty() -> None:
    assert fizzbuzz(0) == []
    assert fizzbuzz(-3) == []
