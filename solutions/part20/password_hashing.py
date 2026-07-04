"""Part 20 練習:密碼雜湊(承 08-password-hashing)。"""

from __future__ import annotations

import hashlib
import hmac
import os


def hash_password(password: str, *, iterations: int = 100_000) -> str:
    """用 PBKDF2-HMAC-SHA256 + 隨機 salt 雜湊密碼。

    回傳 "iterations$salt_hex$hash_hex"。每次呼叫 salt 不同,故雜湊值不同。
    """
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"{iterations}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """驗證密碼是否符合先前 hash_password 的結果(常數時間比較)。"""
    iterations_s, salt_hex, hash_hex = stored.split("$")
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(hash_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations_s))
    return hmac.compare_digest(dk, expected)
