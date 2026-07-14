"""Part 0 ch05：TLS 的三塊積木——雜湊、簽章、對稱/非對稱。

對應章節：chapters/00-backend-foundations/05-https-tls.md
註：憑證簽章用 HMAC 示意「驗章邏輯」，真實 TLS 用非對稱簽章。
"""

from __future__ import annotations

import hashlib
import hmac


def fingerprint(data: bytes) -> str:
    """雜湊：單向指紋。同輸入同輸出、改一點全變、無法還原。"""
    return hashlib.sha256(data).hexdigest()


def ca_sign(ca_secret: bytes, cert: str) -> str:
    """CA 用自己的金鑰對憑證內容蓋章。"""
    return hmac.new(ca_secret, cert.encode(), hashlib.sha256).hexdigest()


def verify_cert(ca_secret: bytes, cert: str, signature: str) -> bool:
    """客戶端驗章：憑證有沒有被竄改？"""
    expected = hmac.new(ca_secret, cert.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
