"""Part 3 練習:dict 操作(承 04-dict)。"""

from __future__ import annotations


def group_by_length(words: list[str]) -> dict[int, list[str]]:
    """依單字長度分組,保留原順序。"""
    out: dict[int, list[str]] = {}
    for w in words:
        out.setdefault(len(w), []).append(w)
    return out


def invert(d: dict[str, int]) -> dict[int, str]:
    """反轉 key/value(假設 value 唯一)。"""
    return {v: k for k, v in d.items()}
