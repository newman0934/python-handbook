"""Part 13（補充）CLI 應用範例：argparse 子命令 + 可程式化解析。純標準庫。"""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="greet", description="打招呼 CLI 工具")
    sub = parser.add_subparsers(dest="command", required=True)

    hello = sub.add_parser("hello", help="打招呼")
    hello.add_argument("name", help="對象")
    hello.add_argument("-c", "--count", type=int, default=1, help="重複次數")
    hello.add_argument("--upper", action="store_true", help="轉大寫")

    bye = sub.add_parser("bye", help="說再見")
    bye.add_argument("name")
    return parser


def run(argv: list[str]) -> str:
    """以程式方式解析並執行（回傳輸出字串，方便測試）。"""
    args = build_parser().parse_args(argv)
    if args.command == "bye":
        return f"Bye, {args.name}!"
    greeting = f"Hello, {args.name}!"
    if args.upper:
        greeting = greeting.upper()
    return "\n".join([greeting] * args.count)
