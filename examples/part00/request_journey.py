"""Part 0 ch01：用裸 socket 手動走一遍 HTTP 請求的旅程（本機、無需外網）。

對應章節：chapters/00-backend-foundations/01-request-journey.md
"""

from __future__ import annotations

import socket
import threading


def serve_once(host: str, port: int, ready: threading.Event) -> None:
    """最小 HTTP 伺服器：accept 一個連線、讀請求、回一段固定回應。"""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)
    ready.set()
    conn, _addr = srv.accept()
    with conn:
        _ = conn.recv(4096)
        body = "Hello from backend!"
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(body.encode())}\r\n"
            "\r\n"
            f"{body}"
        )
        conn.sendall(response.encode())
    srv.close()


def fetch(host: str, port: int) -> tuple[str, str]:
    """裸 socket 客戶端：走完 DNS → TCP → 送請求 → 收回應，回 (status_line, body)。"""
    ip = socket.gethostbyname(host)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    request = f"GET / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    sock.sendall(request.encode())
    raw = b""
    while chunk := sock.recv(4096):
        raw += chunk
    sock.close()
    head, _, body = raw.partition(b"\r\n\r\n")
    status_line = head.split(b"\r\n")[0].decode()
    return status_line, body.decode()


def demo() -> None:
    host, port = "localhost", 8123
    ready = threading.Event()
    server = threading.Thread(target=serve_once, args=(host, port, ready), daemon=True)
    server.start()
    ready.wait(timeout=2)
    status_line, body = fetch(host, port)
    print(f"< {status_line}")
    print(f"< (body) {body}")
    server.join(timeout=2)


if __name__ == "__main__":
    demo()
