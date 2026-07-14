"""Part 14 ch20 測試：ETag 條件請求 + webhook HMAC。"""

from __future__ import annotations

from examples.part14.etag_webhook import (
    is_not_modified,
    make_etag,
    precondition_failed,
    sign_webhook,
    verify_webhook,
)


def test_etag_changes_with_content() -> None:
    assert make_etag(b"a") != make_etag(b"b")
    assert make_etag(b"same") == make_etag(b"same")  # 穩定


def test_if_none_match_hits_returns_not_modified() -> None:
    etag = make_etag(b"payload")
    assert is_not_modified(etag, etag) is True
    assert is_not_modified('"stale"', etag) is False
    assert is_not_modified(None, etag) is False
    assert is_not_modified("*", etag) is True


def test_if_match_optimistic_lock() -> None:
    etag = make_etag(b"v2")
    # 客戶端基於過期版本 → 前置條件失敗（412）
    assert precondition_failed('"v1-old"', etag) is True
    # 客戶端基於最新版本 → 放行
    assert precondition_failed(etag, etag) is False


def test_webhook_signature_roundtrip() -> None:
    secret, payload = b"topsecret", b'{"event":"paid"}'
    sig = sign_webhook(secret, payload)
    assert verify_webhook(secret, payload, sig) is True


def test_webhook_rejects_tampered_payload_and_wrong_secret() -> None:
    secret, payload = b"topsecret", b'{"event":"paid"}'
    sig = sign_webhook(secret, payload)
    assert verify_webhook(secret, payload + b"!", sig) is False  # 竄改內容
    assert verify_webhook(b"wrong", payload, sig) is False       # 錯密鑰
