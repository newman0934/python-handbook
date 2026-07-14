"""Part 14 ch19：RFC 9457 problem+json 統一錯誤契約。

對應章節：chapters/14-web/19-error-contract-rfc9457.md

不是每個 API 各自回不同形狀的錯誤，而是全站共用一個機器可讀、標準化的錯誤格式。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

PROBLEM_CONTENT_TYPE = "application/problem+json"


@dataclass
class Problem(Exception):
    """RFC 9457 問題細節。status/title 必填，其餘選填，extensions 放自訂欄位。"""

    status: int
    title: str
    type: str = "about:blank"
    detail: str | None = None
    instance: str | None = None
    extensions: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        body: dict[str, object] = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
        }
        if self.detail is not None:
            body["detail"] = self.detail
        if self.instance is not None:
            body["instance"] = self.instance
        body.update(self.extensions)  # 擴充成員（如 errors、balance），與標準欄位並列
        return body

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


def insufficient_funds(balance: int, cost: int, path: str) -> Problem:
    """一個具體錯誤：餘額不足。用擴充欄位帶上機器可讀的 balance/cost。"""
    return Problem(
        status=403,
        type="https://example.com/probs/insufficient-funds",
        title="餘額不足",
        detail=f"帳戶餘額 {balance} 不足以支付 {cost}",
        instance=path,
        extensions={"balance": balance, "cost": cost},
    )


def validation_problem(errors: list[dict[str, str]], path: str) -> Problem:
    """驗證失敗：用擴充欄位 errors 帶上逐欄位訊息。"""
    return Problem(
        status=422,
        type="https://example.com/probs/validation-error",
        title="請求驗證失敗",
        instance=path,
        extensions={"errors": errors},
    )


def demo() -> None:
    print("Content-Type:", PROBLEM_CONTENT_TYPE)
    print(insufficient_funds(30, 50, "/accounts/123/pay").to_json())
    print(
        validation_problem(
            [{"field": "email", "message": "格式不正確"}], "/users"
        ).to_json()
    )


if __name__ == "__main__":
    demo()
