"""Part 2（補充）字元編碼與 bytes/str 範例。純標準庫。"""

from __future__ import annotations


def encode_decode_roundtrip(text: str, encoding: str = "utf-8") -> bool:
    """encode 再 decode 應還原（Unicode 三明治的兩端）。"""
    return text.encode(encoding).decode(encoding) == text


def byte_length(text: str, encoding: str = "utf-8") -> int:
    """該編碼下的位元組數（可能 != 字元數）。"""
    return len(text.encode(encoding))


def safe_decode(data: bytes, encoding: str, errors: str = "strict") -> str | None:
    """嘗試以某編碼解碼；strict 下失敗回 None（示範 UnicodeDecodeError）。"""
    try:
        return data.decode(encoding, errors=errors)
    except UnicodeDecodeError:
        return None
