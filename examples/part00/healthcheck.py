"""Part 0 ch10（統整）：一支後端連線自檢腳本。

對應章節：chapters/00-backend-foundations/10-summary.md

把整個 Part 0 串起來：DNS 解析（ch03）、TCP 連線探測（ch02，一個連線=一個 fd ch07）、
從環境變數讀設定（ch09）、行程 PID（ch06）。純標準庫、只打 localhost，不需外部網路。
"""

from __future__ import annotations

import os
import socket


def resolve(host: str) -> list[str]:
    """ch03：把主機名解析成 IP（DNS）。"""
    infos = socket.getaddrinfo(host, None, family=socket.AF_INET)
    return sorted({str(info[4][0]) for info in infos})


def check_tcp_port(host: str, port: int, timeout: float = 0.5) -> bool:
    """ch02 / ch07：試著建一條 TCP 連線（佔一個 fd），能連上代表有人在聽。"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def diagnose(host: str, port: int) -> dict[str, object]:
    """一次回報：我是誰（PID）、目標解析到哪、port 通不通。"""
    return {
        "pid": os.getpid(),
        "target": f"{host}:{port}",
        "resolved_ips": resolve(host),
        "port_open": check_tcp_port(host, port),
    }


def demo() -> None:
    srv = socket.socket()
    srv.bind(("localhost", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    print("有人聽的 port：", diagnose("localhost", port))
    srv.close()
    print("沒人聽的 port：", diagnose("localhost", port))


if __name__ == "__main__":
    demo()
