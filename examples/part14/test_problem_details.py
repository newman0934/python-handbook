"""Part 14 ch19 測試：RFC 9457 problem+json。"""

from __future__ import annotations

import json

from examples.part14.problem_details import (
    PROBLEM_CONTENT_TYPE,
    Problem,
    insufficient_funds,
    validation_problem,
)


def test_content_type_is_problem_json() -> None:
    assert PROBLEM_CONTENT_TYPE == "application/problem+json"


def test_required_members_present() -> None:
    body = Problem(status=404, title="找不到").to_dict()
    assert body["status"] == 404
    assert body["title"] == "找不到"
    assert body["type"] == "about:blank"  # 預設
    assert "detail" not in body  # 選填未給就不出現


def test_extensions_are_flattened_alongside_standard_members() -> None:
    problem = insufficient_funds(balance=30, cost=50, path="/pay")
    body = problem.to_dict()
    # 擴充欄位與標準欄位平級（RFC 9457：extension members 直接放頂層）
    assert body["balance"] == 30
    assert body["cost"] == 50
    assert body["status"] == 403
    assert body["instance"] == "/pay"


def test_to_json_roundtrips() -> None:
    problem = validation_problem([{"field": "email", "message": "格式不正確"}], "/users")
    parsed = json.loads(problem.to_json())
    assert parsed["status"] == 422
    assert parsed["errors"][0]["field"] == "email"


def test_problem_is_raisable_exception() -> None:
    import pytest

    with pytest.raises(Problem) as exc_info:
        raise insufficient_funds(0, 10, "/pay")
    assert exc_info.value.status == 403
