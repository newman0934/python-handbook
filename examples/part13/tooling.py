"""Part 13 工程化與打包的可執行範例。

對應章節：chapters/13-tooling-packaging/
"""

from __future__ import annotations

import re
import tomllib


# --- pip 進階：版本規格解析 ---
def parse_requirement(line: str) -> tuple[str, str]:
    """解析 requirements 行成 (套件名, 版本規格)。"""
    match = re.match(r"([\w.-]+)\s*([=<>~!].*)?$", line.strip())
    if match:
        name = match.group(1)
        spec = match.group(2) or ""
        return name, spec
    return line.strip(), ""


# --- SemVer：版本遞增（打包發佈）---
def next_version(current: str, change_type: str) -> str:
    """依語意化版本計算下一版本。"""
    major, minor, patch = (int(x) for x in current.split("."))
    if change_type == "major":
        return f"{major + 1}.0.0"
    if change_type == "minor":
        return f"{major}.{minor + 1}.0"
    if change_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"未知變更類型: {change_type}")


# --- pyproject.toml 解析 ---
def analyze_pyproject(text: str) -> dict[str, object]:
    """解析 pyproject.toml 的關鍵資訊。"""
    config = tomllib.loads(text)
    project = config.get("project", {})
    optional = project.get("optional-dependencies", {})
    return {
        "name": project.get("name", ""),
        "version": project.get("version", ""),
        "python": project.get("requires-python", ""),
        "deps": project.get("dependencies", []),
        "dev_deps": optional.get("dev", []),
        "build_backend": config.get("build-system", {}).get("build-backend", ""),
    }


# --- 版本規格相容性檢查（簡化）---
def satisfies_spec(version: str, spec: str) -> bool:
    """簡化的版本規格檢查（只處理 == 與 >=）。"""
    if spec.startswith("=="):
        return version == spec[2:]
    if spec.startswith(">="):
        return _version_ge(version, spec[2:])
    return True  # 無規格 = 任意版本


def _version_ge(a: str, b: str) -> bool:
    """a >= b 的版本比較。"""
    pa = tuple(int(x) for x in a.split("."))
    pb = tuple(int(x) for x in b.split("."))
    return pa >= pb
