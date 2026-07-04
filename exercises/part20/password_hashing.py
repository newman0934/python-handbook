"""Part 20 練習:密碼雜湊(承 08-password-hashing)。

實作 hash_password(PBKDF2-HMAC-SHA256 + 隨機 salt,格式 "iters$salt$hash")
與 verify_password(用 hmac.compare_digest 常數時間比較)。
提示:hashlib.pbkdf2_hmac、os.urandom、bytes.hex()/bytes.fromhex()。
"""

from __future__ import annotations


def hash_password(password: str, *, iterations: int = 100_000) -> str:
    """用 PBKDF2-HMAC-SHA256 + 隨機 salt 雜湊密碼。"""
    raise NotImplementedError("實作我!")


def verify_password(password: str, stored: str) -> bool:
    """驗證密碼是否符合先前 hash_password 的結果(常數時間比較)。"""
    raise NotImplementedError("實作我!")
