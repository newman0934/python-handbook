"""Part 11 標準庫的可執行範例。

對應章節：chapters/11-stdlib/
"""

from __future__ import annotations

import csv
import io
import json
import re
import tempfile
import tomllib
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from zoneinfo import ZoneInfo


# --- pathlib ---
def path_parts(path_str: str) -> dict[str, str]:
    # 用 PurePosixPath 讓示範跨平台結果一致（不受 Windows 分隔符影響）
    p = PurePosixPath(path_str)
    return {"name": p.name, "stem": p.stem, "suffix": p.suffix, "parent": str(p.parent)}


# --- datetime：時區轉換 ---
def utc_to_taipei(utc_dt: datetime) -> datetime:
    return utc_dt.astimezone(ZoneInfo("Asia/Taipei"))


def is_aware(dt: datetime) -> bool:
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


# --- json：型別對應陷阱 ---
def json_roundtrip(obj: object) -> object:
    return json.loads(json.dumps(obj))


def encode_with_datetime(obj: dict[str, object]) -> str:
    def default(o: object) -> str:
        if isinstance(o, datetime):
            return o.isoformat()
        raise TypeError(f"無法序列化 {type(o).__name__}")

    return json.dumps(obj, default=default, ensure_ascii=False)


# --- re ---
def extract_dates(text: str) -> list[str]:
    return re.findall(r"\d{4}-\d{2}-\d{2}", text)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# --- csv：正確處理引號 ---
def parse_csv(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


# --- tomllib ---
def parse_toml(text: str) -> dict[str, object]:
    return tomllib.loads(text)


# --- collections.abc ---
def total(nums: Iterable[int]) -> int:
    return sum(nums)


def describe_capabilities(obj: object) -> list[str]:
    caps = []
    if isinstance(obj, Iterable):
        caps.append("iterable")
    if isinstance(obj, Sequence):
        caps.append("sequence")
    return caps


class Playlist(Sequence[str]):
    def __init__(self, songs: list[str]) -> None:
        self._songs = songs

    def __getitem__(self, index: int) -> str:  # type: ignore[override]
        return self._songs[index]

    def __len__(self) -> int:
        return len(self._songs)


# --- tempfile + io：寫讀檔案 ---
def write_and_count_lines(content: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "data.txt"
        path.write_text(content, encoding="utf-8")
        with open(path, encoding="utf-8") as f:
            return sum(1 for _ in f)


def now_utc_is_aware() -> bool:
    return is_aware(datetime.now(UTC))
