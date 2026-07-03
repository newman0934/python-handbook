"""Part 20 範例的驗證測試。

執行：pytest examples/part20
"""

from __future__ import annotations

import pytest

from examples.part20.security import (
    ChatHub,
    SecretStr,
    Snowflake,
    TokenBucket,
    ValidationError,
    base62_decode,
    base62_encode,
    can_delete_post,
    check_csrf,
    escape_html,
    hash_password,
    is_pinned,
    is_safe_fetch_url,
    jwt_sign,
    jwt_verify,
    login_safe,
    safe_deserialize,
    setup_users_db,
    validate_age,
    validate_username,
    verify_integrity,
    verify_password,
)


# --- 輸入驗證（見 01）---
def test_validate_username_allowlist() -> None:
    assert validate_username("alice_01") == "alice_01"
    for bad in ("a", "rm -rf; DROP", "x" * 30, 123):
        with pytest.raises(ValidationError):
            validate_username(bad)


def test_validate_age_rejects_bool() -> None:
    assert validate_age(30) == 30
    with pytest.raises(ValidationError):
        validate_age(True)  # bool 是 int 子類，要排除
    with pytest.raises(ValidationError):
        validate_age(999)


# --- SQL injection：參數化免疫（見 02）---
def test_login_safe_immune_to_injection() -> None:
    conn = setup_users_db()
    assert login_safe(conn, "alice") == ["alice"]
    assert login_safe(conn, "' OR '1'='1") == []  # 注入被當純資料，無效
    conn.close()


# --- RBAC（見 03）---
def test_rbac_and_idor() -> None:
    assert can_delete_post("admin", user_id=1, post_author_id=99) is True
    assert can_delete_post("editor", user_id=2, post_author_id=2) is True
    assert can_delete_post("editor", user_id=2, post_author_id=99) is False  # IDOR 越權
    assert can_delete_post("viewer", user_id=3, post_author_id=3) is False


# --- JWT（見 04）---
def test_jwt_sign_verify_and_tamper() -> None:
    secret = "s3cret"
    token = jwt_sign({"user_id": 42, "role": "admin"}, secret)
    assert jwt_verify(token, secret)["user_id"] == 42
    # 竄改 payload → 簽章對不上
    h, p, s = token.split(".")
    import base64
    import json

    evil = (
        base64.urlsafe_b64encode(json.dumps({"role": "superadmin"}).encode()).rstrip(b"=").decode()
    )
    with pytest.raises(ValueError, match="簽章無效"):
        jwt_verify(f"{h}.{evil}.{s}", secret)
    # 錯誤密鑰
    with pytest.raises(ValueError):
        jwt_verify(token, "wrong")


# --- 密鑰遮罩（見 05）---
def test_secret_str_masks() -> None:
    secret = SecretStr("super-secret")
    assert "super-secret" not in repr(secret)
    assert "super-secret" not in str(secret)
    assert secret.get_secret_value() == "super-secret"


# --- 供應鏈（見 06）---
def test_integrity_and_pinning() -> None:
    content = b"safe package"
    good = __import__("hashlib").sha256(content).hexdigest()
    assert verify_integrity(content, good) is True
    assert verify_integrity(b"tampered", good) is False
    assert is_pinned("fastapi==0.115.0") is True
    assert is_pinned("requests>=2.0") is False


# --- XSS / CSRF / SSRF（見 07）---
def test_xss_escape() -> None:
    out = escape_html("<script>steal()</script>")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_csrf_token() -> None:
    token = "abc123"
    assert check_csrf(token, token) is True
    assert check_csrf(token, "guess") is False


def test_ssrf_allowlist() -> None:
    allow = {"api.example.com"}
    assert is_safe_fetch_url("https://api.example.com/data", allow) is True
    assert is_safe_fetch_url("http://169.254.169.254/meta", allow) is False  # 不在 allowlist
    assert is_safe_fetch_url("http://localhost/admin", allow) is False


# --- 密碼雜湊（見 08）---
def test_password_hashing() -> None:
    stored = hash_password("hunter2")
    assert hash_password("hunter2") != hash_password("hunter2")  # 加鹽 → 每次不同
    assert verify_password("hunter2", stored) is True
    assert verify_password("wrong", stored) is False


# --- 反序列化（見 09）---
def test_safe_deserialize_json_only() -> None:
    assert safe_deserialize('{"user": "alice"}') == {"user": "alice"}


# --- 短網址 base62（見 10）---
@pytest.mark.parametrize("n", [0, 1, 62, 125, 3844, 999999999])
def test_base62_roundtrip(n: int) -> None:
    assert base62_decode(base62_encode(n)) == n


# --- 限流器 token bucket（見 11）---
def test_token_bucket_burst_and_refill() -> None:
    bucket = TokenBucket(capacity=5, refill_rate=1.0, now=0.0)
    assert [bucket.allow(0.0) for _ in range(7)] == [True] * 5 + [False] * 2
    assert bucket.allow(2.0) is True  # 過 2 秒補 2 個
    assert bucket.allow(2.0) is True
    assert bucket.allow(2.0) is False


# --- 聊天 fan-out（見 12）---
def test_chat_fanout_and_offline() -> None:
    hub = ChatHub()
    for user in ("alice", "bob", "carol"):
        hub.connect(user)
        hub.join(user, "general")
    hub.send("alice", "general", "hi")
    assert list(hub.inbox["bob"]) == ["[general] alice: hi"]
    assert list(hub.inbox["alice"]) == []  # 自己不收
    # carol 離線 → 進離線佇列 → 上線補送
    hub.disconnect("carol")
    hub.send("bob", "general", "yo")
    assert list(hub.offline["carol"]) == ["[general] bob: yo"]
    hub.connect("carol")
    assert "[general] bob: yo" in list(hub.inbox["carol"])


# --- 分散式 ID Snowflake（見 13）---
def test_snowflake_unique_ordered_parseable() -> None:
    gen = Snowflake(machine_id=5)
    ids = [gen.next_id(1_700_000_100_000) for _ in range(3)]
    assert len(set(ids)) == 3  # 同毫秒唯一
    assert ids == sorted(ids)  # 遞增
    ts, machine, seq = Snowflake.parse(ids[0])
    assert machine == 5
    assert ts == 1_700_000_100_000
    # 不同機器同時刻不衝突
    a = Snowflake(1).next_id(1_700_000_100_000)
    b = Snowflake(2).next_id(1_700_000_100_000)
    assert a != b


def test_snowflake_clock_rollback() -> None:
    gen = Snowflake(machine_id=1)
    gen.next_id(1_700_000_200_000)
    with pytest.raises(RuntimeError, match="時鐘回撥"):
        gen.next_id(1_700_000_100_000)
