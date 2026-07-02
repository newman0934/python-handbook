"""Part 1 / 03-repl-and-first-program：示範可重用的函式與 __main__ 開關。

對應章節：chapters/01-getting-started/03-repl-and-first-program.md
"""


def greet(name: str) -> str:
    """回傳問候語（可被其他模組 import 重用）。"""
    return f"Hello, {name}!"


def main() -> None:
    print(greet("World"))
    print(f"我被執行了，__name__ = {__name__!r}")


if __name__ == "__main__":
    main()
