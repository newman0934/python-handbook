"""Part 1 / 02-install-and-interpreter：檢查目前 Python 環境資訊。

對應章節：chapters/01-getting-started/02-install-and-interpreter.md
"""

import platform
import sys


def env_summary() -> dict[str, str]:
    """回傳目前直譯器的關鍵資訊。"""
    return {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "executable": sys.executable,
        "is_64bit": str(sys.maxsize > 2**32),
    }


def main() -> None:
    for key, value in env_summary().items():
        print(f"{key:14}: {value}")


if __name__ == "__main__":
    main()
