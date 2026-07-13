#!/usr/bin/env python
"""章節合規檢查（依 CLAUDE.md 規範）。

檢查兩件事：

1. **結構**：每章必備區塊、區塊順序（白話導讀 → 🎯 → Why）、相對連結有效性。
2. **fence 約定**：所有 ```python 區塊必須是**語法合法的 Python**。
   示意片段／語法骨架請改用 ```text，shell 指令用 ```bash，REPL 用 ```pycon。

用法：
    python scripts/check_chapters.py          # 檢查，有問題則 exit 1
"""

from __future__ import annotations

import re
import sys
import textwrap
import warnings
from pathlib import Path

# Windows 主控台預設 cp950，無法輸出 emoji／中文標記
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "chapters"

REQUIRED_SECTIONS = [
    "## 💡 白話導讀",
    "## Why",
    "## Theory",
    "## Specification",
    "## Implementation",
    "## Code Example",
    "## Diagram",
    "## Best Practice",
    "## Common Mistakes",
    "## Interview Notes",
]

# 統整章（NN-summary.md）用專屬結構，不套標準模板
SUMMARY_SECTIONS = [
    "## 🗺️ 知識地圖",
    "## ⚡ 速查表",
    "## 🛠️ 小實作",
    "## ✅ 自測清單",
    "## 🎯 面試速查",
]

# 索引／行為面試型章節：模板允許「依需要增減」
EXEMPT_FROM_SECTIONS = {
    "20-security-system-design/14-behavioral-interview.md",
    "20-security-system-design/15-python-interview-questions.md",
}

PY_BLOCK = re.compile(r"^([ \t]*)```python\n(.*?)^\1```", re.S | re.M)
MD_LINK = re.compile(r"\]\((?!https?://|#|mailto:)([^)\s（）#]+\.md)(?:#[^)]*)?\)")


def check() -> list[str]:
    problems: list[str] = []
    chapters = sorted(CHAPTERS.glob("*/[0-9]*.md"))
    py_blocks = 0

    for path in chapters:
        rel = path.relative_to(CHAPTERS).as_posix()
        text = path.read_text(encoding="utf-8")

        is_summary = path.name.endswith("-summary.md")

        # 1. 必備區塊（統整章用專屬清單）
        if is_summary:
            for section in SUMMARY_SECTIONS:
                if section not in text:
                    problems.append(f"{rel}: 統整章缺區塊 {section}")
        elif rel not in EXEMPT_FROM_SECTIONS:
            for section in REQUIRED_SECTIONS:
                if section not in text:
                    problems.append(f"{rel}: 缺區塊 {section}")

        # 2. 區塊順序：白話導讀 → （🎯）→ Why（統整章不適用）
        if not is_summary:
            i_intro = text.find("## 💡 白話導讀")
            i_usecase = text.find("## 🎯 什麼時候會用到")
            i_why = text.find("## Why")
            if i_intro >= 0 and i_why >= 0 and i_intro > i_why:
                problems.append(f"{rel}: 順序錯——白話導讀應在 Why 之前")
            if i_usecase >= 0 and not (i_intro < i_usecase < i_why):
                problems.append(f"{rel}: 順序錯——🎯 應在導讀之後、Why 之前")

        # 3. 相對連結有效
        for match in MD_LINK.finditer(text):
            if not (path.parent / match.group(1)).resolve().is_file():
                problems.append(f"{rel}: 失效連結 {match.group(1)}")

        # 4. ```python 必須是合法 Python
        for match in PY_BLOCK.finditer(text):
            py_blocks += 1
            code = textwrap.dedent(match.group(2))
            line_no = text[: match.start()].count("\n") + 1
            try:
                # 章節可能刻意示範 `is` 比較字面值等寫法，只驗語法、不理會警告
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    compile(code, f"{rel}:{line_no}", "exec")
            except SyntaxError as exc:
                problems.append(
                    f"{rel}:{line_no}: ```python 區塊語法錯誤——{exc.msg}"
                    f"（若為示意片段請改用 ```text）"
                )

    print(f"檢查 {len(chapters)} 章、{py_blocks} 個 ```python 區塊")
    return problems


def main() -> int:
    problems = check()
    if problems:
        print(f"\n❌ 發現 {len(problems)} 個問題：\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("✅ 全數通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
