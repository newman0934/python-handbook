"""Part 13 範例的驗證測試。

執行：pytest examples/part13
"""

import pytest

from examples.part13.tooling import (
    analyze_pyproject,
    next_version,
    parse_requirement,
    satisfies_spec,
)


@pytest.mark.parametrize(
    ("line", "name", "spec"),
    [
        ("requests==2.31.0", "requests", "==2.31.0"),
        ("numpy>=1.24", "numpy", ">=1.24"),
        ("flask", "flask", ""),
        ("django~=5.0", "django", "~=5.0"),
    ],
)
def test_parse_requirement(line: str, name: str, spec: str) -> None:
    assert parse_requirement(line) == (name, spec)


@pytest.mark.parametrize(
    ("current", "change", "expected"),
    [
        ("1.2.3", "patch", "1.2.4"),
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "major", "2.0.0"),
        ("0.9.9", "patch", "0.9.10"),
    ],
)
def test_next_version(current: str, change: str, expected: str) -> None:
    assert next_version(current, change) == expected


def test_next_version_invalid() -> None:
    with pytest.raises(ValueError, match="未知變更類型"):
        next_version("1.0.0", "unknown")


def test_analyze_pyproject() -> None:
    text = """
[project]
name = "my-package"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["requests>=2.28", "click>=8.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.6"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
"""
    info = analyze_pyproject(text)
    assert info["name"] == "my-package"
    assert info["version"] == "0.1.0"
    assert info["python"] == ">=3.12"
    assert info["deps"] == ["requests>=2.28", "click>=8.0"]
    assert info["dev_deps"] == ["pytest>=8.0", "ruff>=0.6"]
    assert info["build_backend"] == "setuptools.build_meta"


@pytest.mark.parametrize(
    ("version", "spec", "expected"),
    [
        ("2.31.0", "==2.31.0", True),
        ("2.30.0", "==2.31.0", False),
        ("1.25.0", ">=1.24", True),
        ("1.23.0", ">=1.24", False),
        ("3.0.0", "", True),  # 無規格 = 任意
    ],
)
def test_satisfies_spec(version: str, spec: str, expected: bool) -> None:
    assert satisfies_spec(version, spec) is expected
