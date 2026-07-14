"""Part 14 ch20：ETag 條件請求 + webhook HMAC 簽章。

對應章節：chapters/14-web/20-etag-conditional-webhook.md

ETag：用內容雜湊當「版本指紋」，讓客戶端問「還是這版嗎？」沒變就回 304 省頻寬。
webhook：你送事件給別人時用 HMAC 簽章，讓對方能驗「這真的是我送的、沒被竄改」。
"""

from __future__ import annotations

import hashlib
import hmac


def make_etag(body: bytes) -> str:
    """用內容雜湊產生強 ETag（內容變 → ETag 變）。"""
    return '"' + hashlib.sha256(body).hexdigest()[:16] + '"'


def is_not_modified(if_none_match: str | None, current_etag: str) -> bool:
    """處理 If-None-Match：客戶端手上的版本仍是最新 → True（回 304）。"""
    if not if_none_match:
        return False
    tags = [t.strip() for t in if_none_match.split(",")]
    return current_etag in tags or "*" in tags


def precondition_failed(if_match: str | None, current_etag: str) -> bool:
    """處理 If-Match（樂觀鎖）：客戶端基於的版本已過期 → True（回 412）。"""
    if not if_match:
        return False
    tags = [t.strip() for t in if_match.split(",")]
    return current_etag not in tags and "*" not in tags


def sign_webhook(secret: bytes, payload: bytes) -> str:
    """用 HMAC-SHA256 對 payload 簽章（送 webhook 時放進 header）。"""
    return "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()


def verify_webhook(secret: bytes, payload: bytes, signature: str) -> bool:
    """驗證 webhook 簽章；用 compare_digest 防時序攻擊。"""
    expected = sign_webhook(secret, payload)
    return hmac.compare_digest(expected, signature)


def demo() -> None:
    body = b'{"id":1,"name":"ada"}'
    etag = make_etag(body)
    print("ETag:", etag)
    print("手上是最新版 → 回 304?", is_not_modified(etag, etag))
    print("手上是舊版 → 回 304?", is_not_modified('"old"', etag))
    sig = sign_webhook(b"secret", body)
    print("簽章:", sig)
    print("驗證正確簽章:", verify_webhook(b"secret", body, sig))
    print("驗證被竄改的 payload:", verify_webhook(b"secret", body + b"x", sig))


if __name__ == "__main__":
    demo()
