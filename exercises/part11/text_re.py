"""Part 11 練習:re 文字處理(承 05-re)。

實作 extract_numbers(用 re.findall 抽整數,含負號)與 slugify
(小寫、非英數字換 '-'、去頭尾 '-')。
"""

from __future__ import annotations


def extract_numbers(text: str) -> list[int]:
    """抽出文字中所有整數(可含負號),依出現順序。"""
    raise NotImplementedError("實作我!")


def slugify(text: str) -> str:
    """轉成 URL slug:小寫、非英數字換成 '-'、去頭尾多餘 '-'。"""
    raise NotImplementedError("實作我!")
