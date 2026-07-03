"""Part 12（補充）屬性測試待測函式：run-length 編解碼。純標準庫。"""

from __future__ import annotations


def rle_encode(s: str) -> list[tuple[str, int]]:
    if not s:
        return []
    result: list[tuple[str, int]] = []
    count = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            count += 1
        else:
            result.append((s[i - 1], count))
            count = 1
    result.append((s[-1], count))
    return result


def rle_decode(pairs: list[tuple[str, int]]) -> str:
    return "".join(ch * n for ch, n in pairs)
