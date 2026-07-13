"""Part 0 ch03：域名如何變成 IP:Port。

對應章節：chapters/00-backend-foundations/03-dns-ip-port.md
"""

from __future__ import annotations

import socket


def resolve(host: str) -> list[str]:
    """DNS 正解：主機名 → 一或多個 IPv4（可能有多個：負載平衡 / CDN）。"""
    infos = socket.getaddrinfo(host, None, family=socket.AF_INET)
    return sorted({str(info[4][0]) for info in infos})


def free_port() -> int:
    """綁 port 0 → 讓 OS 分配一個空閒 port（測試常用手法）。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("localhost", 0))
        port: int = sock.getsockname()[1]
        return port


def demo() -> None:
    print(f"localhost → {resolve('localhost')}")
    try:
        print(f"example.com → {resolve('example.com')}")
    except socket.gaierror as exc:
        print(f"example.com → 解析失敗（此環境無外網）: {exc}")
    print(f"free_port → {free_port()}")


if __name__ == "__main__":
    demo()
