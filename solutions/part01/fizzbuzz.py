"""Part 1 練習:FizzBuzz(承 03-repl-and-first-program)。"""

from __future__ import annotations


def fizzbuzz(n: int) -> list[str]:
    """回傳 1..n 的 FizzBuzz 序列(list[str])。

    規則:3 的倍數 -> "Fizz";5 的倍數 -> "Buzz";
    15 的倍數 -> "FizzBuzz";其餘 -> 該數字的字串。n<=0 回空 list。
    """
    out: list[str] = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            out.append("FizzBuzz")
        elif i % 3 == 0:
            out.append("Fizz")
        elif i % 5 == 0:
            out.append("Buzz")
        else:
            out.append(str(i))
    return out
