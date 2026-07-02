"""Part 1 / 01-why-python：用少少幾行體會 Python 的開發效率。

對應章節：chapters/01-getting-started/01-why-python.md
"""

from collections import Counter


def top_words(text: str, n: int = 3) -> list[tuple[str, int]]:
    """回傳出現次數最多的 n 個單字（不分大小寫）。"""
    words = text.lower().split()
    return Counter(words).most_common(n)


def main() -> None:
    sample = "the quick brown fox the lazy dog the end"
    for word, count in top_words(sample):
        print(f"{word}: {count}")


if __name__ == "__main__":
    main()
