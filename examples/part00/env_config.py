"""Part 0 ch09：從環境變數載入設定（12-factor 的 config 原則）。

對應章節：chapters/00-backend-foundations/09-shell-env-diagnostics.md

重點：設定來自環境變數，不寫死在程式碼裡；缺必要值就「開機即失敗」（fail fast），
而不是跑到一半才炸。
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


class ConfigError(Exception):
    """設定不合法：缺必要值，或型別轉不過去。"""


def _get_bool(env: Mapping[str, str], key: str, default: bool) -> bool:
    raw = env.get(key)
    if raw is None:
        return default
    # 環境變數永遠是字串，"false"/"0" 都是非空字串，不能直接當 bool 用
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(env: Mapping[str, str], key: str, default: int) -> int:
    raw = env.get(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as e:
        raise ConfigError(f"環境變數 {key}={raw!r} 不是合法整數") from e


@dataclass(frozen=True)
class Config:
    database_url: str
    port: int
    debug: bool


def load_config(env: Mapping[str, str] | None = None) -> Config:
    """從環境變數組出設定；缺 DATABASE_URL 直接開機失敗。"""
    env = os.environ if env is None else env
    url = env.get("DATABASE_URL")
    if not url:
        raise ConfigError("缺少必要環境變數 DATABASE_URL")
    return Config(
        database_url=url,
        port=_get_int(env, "PORT", 8000),
        debug=_get_bool(env, "DEBUG", False),
    )


def demo() -> None:
    fake_env = {"DATABASE_URL": "postgres://localhost/app", "PORT": "5432", "DEBUG": "true"}
    print("載入設定：", load_config(fake_env))
    for bad in ({}, {"DATABASE_URL": "x", "PORT": "abc"}):
        try:
            load_config(bad)
        except ConfigError as e:
            print("開機即失敗：", e)


if __name__ == "__main__":
    demo()
