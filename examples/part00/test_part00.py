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


def test_fingerprint_is_deterministic_and_sensitive() -> None:
    from examples.part00.tls_building_blocks import fingerprint

    # 確定性：同輸入同輸出
    assert fingerprint(b"hello") == fingerprint(b"hello")
    # 敏感性：改一個字母，指紋完全不同
    assert fingerprint(b"hello") != fingerprint(b"hellp")


def test_cert_verification_catches_tampering() -> None:
    import secrets

    from examples.part00.tls_building_blocks import ca_sign, verify_cert

    ca_secret = secrets.token_bytes(32)
    cert = "CN=api.example.com; pubkey=ABC123"
    signature = ca_sign(ca_secret, cert)

    # 未竄改：驗章通過
    assert verify_cert(ca_secret, cert, signature) is True
    # 中間人竄改域名：驗章失敗，擋下冒充
    tampered = cert.replace("api.example.com", "evil.com")
    assert verify_cert(ca_secret, tampered, signature) is False


def test_threads_share_memory() -> None:
    from examples.part00.process_vs_thread import collect_via_threads

    # 3 個執行緒都 append 到同一份 list（共享記憶體）→ 收集到 3 個值
    result = collect_via_threads(3)
    assert sorted(result) == [0, 1, 2]


def test_process_is_isolated() -> None:
    import os

    from examples.part00.process_vs_thread import child_report

    report = child_report()
    # 子行程有不同的 PID（是另一個行程）
    assert report["child_pid"] != os.getpid()
    # 子行程改的是它「自己的」list
    assert report["child_list"] == [999, 123]


def test_everything_has_an_fd() -> None:
    from examples.part00.file_descriptor import file_fd, pipe_fds, socket_fd

    # 檔案、socket、pipe 都拿到一個非負整數 fd
    assert file_fd() >= 0
    assert socket_fd() >= 0
    read_fd, write_fd = pipe_fds()
    assert read_fd >= 0 and write_fd >= 0


def test_nonblocking_accept_does_not_block() -> None:
    from examples.part00.file_descriptor import nonblocking_accept_raises

    # 非阻塞 accept 沒人連時「立刻」拋例外，不卡住 —— asyncio 的地基
    assert nonblocking_accept_raises() is True
