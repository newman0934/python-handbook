"""Part 11 練習:re 文字處理(承 05-re)。"""

from __future__ import annotations

import re


def extract_numbers(text: str) -> list[int]:
    """抽出文字中所有整數(可含負號),依出現順序。"""
    return [int(m) for m in re.findall(r"-?\d+", text)]


def slugify(text: str) -> str:
    """轉成 URL slug:小寫、非英數字換成 '-'、去頭尾多餘 '-'。"""
    lowered = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    return slug.strip("-")
