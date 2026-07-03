"""Part 2（補充）字元編碼範例的驗證測試。"""

from __future__ import annotations

from examples.part02.encoding import (
    byte_length,
    encode_decode_roundtrip,
    safe_decode,
)


def test_roundtrip() -> None:
    for text in ("café", "中文", "\U0001f44d", "ascii", ""):
        assert encode_decode_roundtrip(text) is True


def test_byte_length_differs_from_char_length() -> None:
    assert len("café") == 4
    assert byte_length("café", "utf-8") == 5  # é 佔 2 bytes
    assert byte_length("\U0001f44d", "utf-8") == 4  # emoji 佔 4 bytes


def test_safe_decode_wrong_encoding() -> None:
    utf8 = "café".encode()
    assert safe_decode(utf8, "ascii") is None  # 用錯編碼 → 攔下
    assert safe_decode(utf8, "utf-8") == "café"  # 正確編碼 → 還原
    assert safe_decode(utf8, "ascii", errors="ignore") == "caf"  # 忽略壞位元組
