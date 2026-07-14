"""Part 0 ch04：手動組裝與解析 HTTP 報文。

對應章節：chapters/00-backend-foundations/04-http-messages.md
"""

from __future__ import annotations


def build_request(method: str, path: str, host: str, body: str = "") -> bytes:
    """組一個 HTTP 請求報文（就是純文字 + CRLF）。"""
    lines = [f"{method} {path} HTTP/1.1", f"Host: {host}"]
    if body:
        lines.append("Content-Type: application/json")
        lines.append(f"Content-Length: {len(body.encode())}")
    lines.append("")
    lines.append(body)
    return "\r\n".join(lines).encode()


def parse_response(raw: bytes) -> dict[str, object]:
    """解析 HTTP 回應報文 → 拆出 status、headers、body。"""
    head, _, body = raw.partition(b"\r\n\r\n")
    lines = head.decode().split("\r\n")
    version, status_code, *reason = lines[0].split(" ")
    headers: dict[str, str] = {}
    for line in lines[1:]:
        key, _, value = line.partition(": ")
        headers[key] = value
    return {
        "version": version,
        "status": int(status_code),
        "reason": " ".join(reason),
        "headers": headers,
        "body": body.decode(),
    }
