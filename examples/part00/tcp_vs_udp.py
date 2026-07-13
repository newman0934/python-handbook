"""Part 0 ch02：TCP（連線導向、可靠）vs UDP（無連線、射後不理）。

對應章節：chapters/00-backend-foundations/02-tcp-udp.md
"""

from __future__ import annotations

import socket
import threading


def tcp_echo_server(port: int, ready: threading.Event) -> None:
    """TCP 伺服器：收到什麼就回大寫（證明有收到、有回應）。"""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("localhost", port))
    srv.listen(1)
    ready.set()
    conn, _ = srv.accept()
    with conn:
        while data := conn.recv(1024):
            conn.sendall(data.upper())
    srv.close()


def tcp_roundtrip(port: int, messages: list[bytes]) -> list[bytes]:
    """對 TCP echo server 送一串訊息，回傳每次收到的回應。"""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", port))
    replies: list[bytes] = []
    for msg in messages:
        client.sendall(msg)
        replies.append(client.recv(1024))
    client.close()
    return replies


def udp_server(port: int, ready: threading.Event, box: list[bytes]) -> None:
    """UDP 伺服器：收到什麼就記下來（不回覆——射後不理）。"""
    srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    srv.bind(("localhost", port))
    ready.set()
    srv.settimeout(1.0)
    try:
        while True:
            data, _ = srv.recvfrom(1024)
            box.append(data)
    except TimeoutError:
        pass
    srv.close()


def udp_send(port: int, messages: list[bytes]) -> None:
    """UDP 送出一串訊息，不等任何確認。"""
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for msg in messages:
        client.sendto(msg, ("localhost", port))
    client.close()
