"""Part 0 範例的驗證測試。

執行：pytest examples/part00
"""

from __future__ import annotations

import socket
import threading

from examples.part00.request_journey import fetch, serve_once


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        port: int = s.getsockname()[1]
        return port


def test_fetch_walks_the_journey() -> None:
    host, port = "localhost", _free_port()
    ready = threading.Event()
    server = threading.Thread(target=serve_once, args=(host, port, ready), daemon=True)
    server.start()
    assert ready.wait(timeout=3)

    status_line, body = fetch(host, port)

    assert status_line == "HTTP/1.1 200 OK"
    assert body == "Hello from backend!"
    server.join(timeout=3)
