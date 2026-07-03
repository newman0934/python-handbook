"""Part 20 安全與系統設計範例：輸入驗證 / 參數化查詢 / RBAC / JWT /
密鑰遮罩 / 供應鏈雜湊 / XSS·CSRF·SSRF / 密碼雜湊 / 反序列化 /
短網址 / 限流器 / 聊天 fan-out / 分散式 ID。

全部純 stdlib，封裝可驗證的確定性邏輯。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import ipaddress
import json
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from urllib.parse import urlparse

# ===== 輸入驗證：allowlist（見 01）=====
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


class ValidationError(Exception):
    pass


def validate_username(username: object) -> str:
    if not isinstance(username, str) or not _USERNAME_RE.match(username):
        raise ValidationError("username 只允許 3-20 個字母/數字/底線")
    return username


def validate_age(age: object) -> int:
    if not isinstance(age, int) or isinstance(age, bool) or not (0 <= age <= 150):
        raise ValidationError("age 必須是 0-150 的整數")
    return age


# ===== SQL injection：參數化查詢（見 02）=====
def setup_users_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.executemany("INSERT INTO users (name) VALUES (?)", [("alice",), ("bob",)])
    conn.commit()
    return conn


def login_safe(conn: sqlite3.Connection, username: str) -> list[str]:
    """參數化：輸入永遠是純資料，免疫 injection。"""
    return [row[0] for row in conn.execute("SELECT name FROM users WHERE name = ?", (username,))]


# ===== RBAC 授權（見 03）=====
_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"post:delete_any"},
    "editor": {"post:delete_own"},
    "viewer": set(),
}


def can_delete_post(role: str, user_id: int, post_author_id: int) -> bool:
    """功能權限 + 資源歸屬（防 IDOR）。"""
    perms = _ROLE_PERMISSIONS.get(role, set())
    if "post:delete_any" in perms:
        return True
    return "post:delete_own" in perms and user_id == post_author_id


# ===== JWT（HS256）（見 04）=====
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def jwt_sign(payload: dict[str, object], secret: str, exp_seconds: int = 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    body = {**payload, "exp": int(time.time()) + exp_seconds}
    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(body, separators=(",", ":")).encode())
    sig = hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url(sig)}"


def jwt_verify(token: str, secret: str) -> dict[str, object]:
    try:
        h, p, s = token.split(".")
    except ValueError:
        raise ValueError("token 格式錯誤") from None
    expected = hmac.new(secret.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _b64url_decode(s)):
        raise ValueError("簽章無效")
    body: dict[str, object] = json.loads(_b64url_decode(p))
    return body


# ===== 密鑰遮罩（見 05）=====
class SecretStr:
    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def get_secret_value(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "SecretStr('**********')" if self._value else "SecretStr('')"

    __str__ = __repr__


# ===== 供應鏈：完整性雜湊 + 版本釘死（見 06）=====
def verify_integrity(content: bytes, expected_hash: str) -> bool:
    return hashlib.sha256(content).hexdigest() == expected_hash


def is_pinned(spec: str) -> bool:
    return "==" in spec and not any(op in spec for op in (">=", "<=", "*", "~", "^"))


# ===== XSS / CSRF / SSRF（見 07）=====
def escape_html(comment: str) -> str:
    return f"<div>{html.escape(comment)}</div>"


def check_csrf(session_token: str, form_token: str) -> bool:
    return secrets.compare_digest(session_token, form_token)


def is_safe_fetch_url(url: str, allowed_hosts: set[str]) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.hostname is None:
        return False
    if parsed.hostname not in allowed_hosts:
        return False
    try:
        ip = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        return True  # 主機名在 allowlist 內、非直接 IP，視為可信
    return not (ip.is_private or ip.is_loopback or ip.is_link_local)


# ===== 密碼雜湊：scrypt + 鹽（見 08）=====
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _algo, salt_b64, hash_b64 = stored.split("$")
    except ValueError:
        return False
    salt, expected = base64.b64decode(salt_b64), base64.b64decode(hash_b64)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=len(expected))
    return hmac.compare_digest(dk, expected)


# ===== 反序列化：只用 JSON 還原不可信資料（見 09）=====
def safe_deserialize(data: str) -> object:
    """只用 JSON 還原資料（不執行程式碼）；絕不對不可信資料用 pickle。"""
    return json.loads(data)


# ===== 短網址：base62（見 10）=====
_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_BASE = len(_ALPHABET)


def base62_encode(n: int) -> str:
    if n == 0:
        return _ALPHABET[0]
    chars: list[str] = []
    while n > 0:
        n, r = divmod(n, _BASE)
        chars.append(_ALPHABET[r])
    return "".join(reversed(chars))


def base62_decode(code: str) -> int:
    n = 0
    for ch in code:
        n = n * _BASE + _ALPHABET.index(ch)
    return n


# ===== 限流器：token bucket（見 11）=====
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float, now: float = 0.0) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last = now

    def allow(self, now: float) -> bool:
        self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.refill_rate)
        self.last = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


# ===== 聊天 fan-out（見 12）=====
@dataclass
class ChatHub:
    rooms: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    inbox: dict[str, deque[str]] = field(default_factory=lambda: defaultdict(deque))
    offline: dict[str, deque[str]] = field(default_factory=lambda: defaultdict(deque))
    online: set[str] = field(default_factory=set)

    def connect(self, user: str) -> None:
        self.online.add(user)
        while self.offline[user]:
            self.inbox[user].append(self.offline[user].popleft())

    def disconnect(self, user: str) -> None:
        self.online.discard(user)

    def join(self, user: str, room: str) -> None:
        self.rooms[room].add(user)

    def send(self, sender: str, room: str, text: str) -> None:
        msg = f"[{room}] {sender}: {text}"
        for member in sorted(self.rooms[room]):
            if member == sender:
                continue
            target = self.inbox if member in self.online else self.offline
            target[member].append(msg)


# ===== 分散式 ID：Snowflake（見 13）=====
_MACHINE_BITS, _SEQUENCE_BITS = 10, 12
_MAX_SEQUENCE = (1 << _SEQUENCE_BITS) - 1
_SNOWFLAKE_EPOCH = 1_700_000_000_000


class Snowflake:
    def __init__(self, machine_id: int) -> None:
        self.machine_id = machine_id
        self.last_ts = -1
        self.sequence = 0

    def next_id(self, now_ms: int) -> int:
        if now_ms < self.last_ts:
            raise RuntimeError(f"時鐘回撥：now={now_ms} < last={self.last_ts}")
        if now_ms == self.last_ts:
            self.sequence = (self.sequence + 1) & _MAX_SEQUENCE
            if self.sequence == 0:
                now_ms += 1
        else:
            self.sequence = 0
        self.last_ts = now_ms
        return (
            ((now_ms - _SNOWFLAKE_EPOCH) << (_MACHINE_BITS + _SEQUENCE_BITS))
            | (self.machine_id << _SEQUENCE_BITS)
            | self.sequence
        )

    @staticmethod
    def parse(snowflake_id: int) -> tuple[int, int, int]:
        seq = snowflake_id & _MAX_SEQUENCE
        machine = (snowflake_id >> _SEQUENCE_BITS) & ((1 << _MACHINE_BITS) - 1)
        ts = (snowflake_id >> (_MACHINE_BITS + _SEQUENCE_BITS)) + _SNOWFLAKE_EPOCH
        return ts, machine, seq
