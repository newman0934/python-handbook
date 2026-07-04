"""Part 1 練習:字頻統計(承 03-repl-and-first-program)。"""

from __future__ import annotations


def word_frequency(text: str) -> dict[str, int]:
    """統計 text 中每個單字出現次數(大小寫不敏感)。

    以空白切分;單字轉小寫;回傳 {word: count}。空字串回空 dict。
    """
    counts: dict[str, int] = {}
    for word in text.lower().split():
        counts[word] = counts.get(word, 0) + 1
    return counts
