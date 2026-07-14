"""Part 0 ch07：一切皆 fd + 阻塞 vs 非阻塞。

對應章節：chapters/00-backend-foundations/07-file-descriptor-io.md
"""

from __future__ import annotations

import os
import socket
import tempfile


def file_fd() -> int:
    """開一個檔案，回傳它的 fd（一個非負小整數）。"""
    with tempfile.NamedTemporaryFile() as tmp:
        return tmp.fileno()


def socket_fd() -> int:
    """開一個 socket，回傳它的 fd（socket 也是『檔案』）。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.fileno()


def nonblocking_accept_raises() -> bool:
    """非阻塞 socket 在沒人連線時 accept() 會立刻拋 BlockingIOError。"""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("localhost", 0))
    srv.listen(1)
    srv.setblocking(False)
    try:
        srv.accept()
        return False
    except BlockingIOError:
        return True
    finally:
        srv.close()


def pipe_fds() -> tuple[int, int]:
    """開一個 pipe，回傳（讀端 fd, 寫端 fd）。"""
    read_fd, write_fd = os.pipe()
    os.close(read_fd)
    os.close(write_fd)
    return read_fd, write_fd
