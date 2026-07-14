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


def test_tcp_is_reliable_and_replies() -> None:
    from examples.part00.tcp_vs_udp import tcp_echo_server, tcp_roundtrip

    port = _free_port()
    ready = threading.Event()
    threading.Thread(target=tcp_echo_server, args=(port, ready), daemon=True).start()
    assert ready.wait(timeout=3)

    replies = tcp_roundtrip(port, [b"hello", b"world"])

    # TCP 保序、可靠：每次都收到對應的大寫回應
    assert replies == [b"HELLO", b"WORLD"]


def test_udp_is_fire_and_forget() -> None:
    import time

    from examples.part00.tcp_vs_udp import udp_send, udp_server

    port = _free_port()
    ready = threading.Event()
    box: list[bytes] = []
    threading.Thread(target=udp_server, args=(port, ready, box), daemon=True).start()
    assert ready.wait(timeout=3)

    udp_send(port, [b"packet-1", b"packet-2", b"packet-3"])
    time.sleep(1.2)  # 等 UDP server 收完（localhost 幾乎不丟）

    assert box == [b"packet-1", b"packet-2", b"packet-3"]


def test_resolve_localhost() -> None:
    from examples.part00.dns_ip_port import resolve

    # localhost 走 hosts 檔，不依賴外部 DNS，CI 穩定
    assert resolve("localhost") == ["127.0.0.1"]


def test_free_port_is_valid_and_bindable() -> None:
    from examples.part00.dns_ip_port import free_port

    port = free_port()
    assert 1024 <= port <= 65535
    # 分配到的 port 應該可以再綁（證明它當下是空閒的）
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("localhost", port))


def test_build_request_has_four_parts() -> None:
    from examples.part00.http_messages import build_request

    raw = build_request("POST", "/tasks", "api.example.com", '{"title":"x"}')
    text = raw.decode()
    # 起始行、Host header、空行分界、body
    assert text.startswith("POST /tasks HTTP/1.1\r\n")
    assert "Host: api.example.com\r\n" in text
    assert "\r\n\r\n" in text  # header 與 body 的分界
    assert text.endswith('{"title":"x"}')


def test_parse_response() -> None:
    from examples.part00.http_messages import parse_response

    raw = (
        b"HTTP/1.1 201 Created\r\n"
        b"Content-Type: application/json\r\n"
        b"\r\n"
        b'{"id":1}'
    )
    parsed = parse_response(raw)
    assert parsed["status"] == 201
    assert parsed["reason"] == "Created"
    assert parsed["headers"] == {"Content-Type": "application/json"}
    assert parsed["body"] == '{"id":1}'
