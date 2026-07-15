#!/usr/bin/env python
"""導覽與計數維護工具（安全版）。

設計取捨:全書既有 footer 的標點本來就不統一(半/全形冒號、emoji 變異選擇子、
`---` 有無),若「全自動重寫」會churn 近 400 章的標點、動到手寫內容。因此本工具:

  1. 計數 —— **自動修正**(唯一真正會出 bug 的地方,且改動極小):
     chapters/README.md 的章數欄、CLAUDE.md 的全書章數。
  2. 導覽連結 —— **只檢查、不重寫**:每章的「下一章 / 下一 Part」連結是否指向正確的
     檔案;Part README 是否列出該 Part 每一章且連結正確。發現問題就回報,標點風格不動。

新增章節時:照鄰章樣式補一行 footer + README 列,再跑本工具,它會立刻告訴你有沒有接錯。

用法:
  python scripts/gen_nav.py          # 檢查(計數不符也只回報),有問題非零退出
  python scripts/gen_nav.py --fix    # 自動修正計數,再檢查導覽連結
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "chapters"
CLAUDE_MD = ROOT / "CLAUDE.md"

# 容忍格式變體:➡ ⬅ 可帶或不帶 emoji 變異選擇子(U+FE0F)。
_FWD = re.compile(r"^➡️?\s")  # 「下一章 / 下一 Part」那一行
_LINK = re.compile(r"\]\(([^)]+)\)")  # 取 markdown 連結目標


def part_dirs() -> list[Path]:
    return sorted(
        d for d in CHAPTERS.iterdir() if d.is_dir() and re.match(r"\d{2}-", d.name)
    )


def chapter_files(part: Path) -> list[Path]:
    return sorted(f for f in part.glob("[0-9]*.md") if f.name != "README.md")


# ── 1. 計數(可自動修正)──────────────────────────────────────────


def plan_counts(parts: list[Path]) -> dict[Path, str]:
    changes: dict[Path, str] = {}
    md = (CHAPTERS / "README.md").read_text(encoding="utf-8")
    new_md = md
    for part in parts:
        n = len(chapter_files(part))
        new_md = re.sub(
            rf"(\[[^\]]+\]\({part.name}/\) \| )\d+( \|)", rf"\g<1>{n}\g<2>", new_md
        )
    if new_md != md:
        changes[CHAPTERS / "README.md"] = new_md

    total = sum(len(chapter_files(p)) for p in parts)
    cm = CLAUDE_MD.read_text(encoding="utf-8")
    new_cm = re.sub(r"（\d+ 章）", f"（{total} 章）", cm)
    if new_cm != cm:
        changes[CLAUDE_MD] = new_cm
    return changes


# ── 2. 導覽連結檢查(只回報)──────────────────────────────────────


def _footer_forward_target(text: str) -> str | None:
    """取 footer 裡最後一個『➡️ …』行的連結目標(容忍標點差異)。"""
    target = None
    for line in text.splitlines():
        if _FWD.match(line.lstrip()):
            m = _LINK.search(line)
            if m:
                target = m.group(1).strip()
    return target


def check_footers(parts: list[Path]) -> list[str]:
    issues: list[str] = []
    for pi, part in enumerate(parts):
        files = chapter_files(part)
        for ci, f in enumerate(files):
            rel = f.relative_to(ROOT)
            text = f.read_text(encoding="utf-8")
            target = _footer_forward_target(text)
            if ci + 1 < len(files):  # 應指向下一章
                expect = files[ci + 1].name
                if target != expect:
                    issues.append(
                        f"{rel}: 下一章連結應為 {expect},實際為 {target or '缺'}"
                    )
            elif pi + 1 < len(parts):  # 該 Part 最後一章 → 應指向下一 Part
                expect = f"../{parts[pi + 1].name}/README.md"
                if target != expect:
                    issues.append(
                        f"{rel}: 下一 Part 連結應為 {expect},實際為 {target or '缺'}"
                    )
            # 全書最後一章不檢查(無下一步)
    return issues


def check_part_readmes(parts: list[Path]) -> tuple[list[str], list[Path]]:
    issues: list[str] = []
    skipped: list[Path] = []
    for part in parts:
        readme = part / "README.md"
        if not readme.exists():
            issues.append(f"{readme.relative_to(ROOT)}: 缺少 Part 索引 README.md")
            continue
        text = readme.read_text(encoding="utf-8")
        if text.count("| 章 | 標題 |") != 1:
            skipped.append(readme)  # 非標準結構(如 Part 15 雙表格)→ 不自動檢查
            continue
        linked = {
            m.group(1).strip()
            for line in text.splitlines()
            if line.lstrip().startswith("|")
            for m in [_LINK.search(line)]
            if m and m.group(1).strip().endswith(".md")
        }
        actual = {f.name for f in chapter_files(part)}
        missing = actual - linked
        extra = linked - actual
        rel = readme.relative_to(ROOT)
        if missing:
            issues.append(f"{rel}: README 未列出章節 {sorted(missing)}")
        if extra:
            issues.append(f"{rel}: README 連到不存在的檔案 {sorted(extra)}")
    return issues, skipped


def main() -> int:
    fix = "--fix" in sys.argv[1:]
    parts = part_dirs()
    total_ch = sum(len(chapter_files(p)) for p in parts)
    print(f"掃描 {len(parts)} 個 Part、{total_ch} 章")

    # 1. 計數
    count_changes = plan_counts(parts)
    if count_changes and fix:
        for path, content in count_changes.items():
            path.write_text(content, encoding="utf-8")
        print(f"✅ 已修正計數:{', '.join(p.name for p in count_changes)}")
        count_changes = {}

    # 2. 檢查
    footer_issues = check_footers(parts)
    readme_issues, readme_skipped = check_part_readmes(parts)

    if readme_skipped:
        print(f"  (略過非標準 README {len(readme_skipped)} 個,需手動維護:"
              f"{', '.join(str(p.relative_to(ROOT)) for p in readme_skipped)})")

    problems: list[str] = []
    if count_changes:
        problems.append(
            f"計數過時(執行 --fix 修正):{', '.join(p.name for p in count_changes)}"
        )
    problems += footer_issues
    problems += readme_issues

    if not problems:
        print("✅ 導覽連結與計數皆一致。")
        return 0

    print(f"❌ 發現 {len(problems)} 個問題:")
    for p in problems:
        print(f"    - {p}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
