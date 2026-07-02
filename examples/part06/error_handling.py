"""Part 6 錯誤處理的可執行範例。

對應章節：chapters/06-error-handling/
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, suppress
from types import TracebackType


# --- 自訂例外階層 ---
class BankError(Exception):
    """銀行操作錯誤基底。"""


class AccountNotFoundError(BankError):
    def __init__(self, account_id: int) -> None:
        self.account_id = account_id
        super().__init__(f"帳戶不存在: {account_id}")


class InsufficientFundsError(BankError):
    def __init__(self, balance: float, amount: float) -> None:
        self.balance = balance
        self.amount = amount
        self.shortfall = amount - balance
        super().__init__(f"餘額不足：{balance} < {amount}")


class Bank:
    def __init__(self) -> None:
        self._accounts: dict[int, float] = {1: 100.0}

    def withdraw(self, account_id: int, amount: float) -> float:
        if account_id not in self._accounts:
            raise AccountNotFoundError(account_id)
        balance = self._accounts[account_id]
        if amount > balance:
            raise InsufficientFundsError(balance, amount)
        self._accounts[account_id] = balance - amount
        return self._accounts[account_id]


# --- 例外鏈 ---
class ConfigError(Exception):
    pass


def load_config(text: str) -> dict[str, object]:
    """轉換底層例外，保留原因。"""
    try:
        result: dict[str, object] = json.loads(text)
        return result
    except json.JSONDecodeError as e:
        raise ConfigError("設定不是合法 JSON") from e


# --- try/except/else/finally ---
def safe_divide(a: float, b: float) -> float | None:
    log: list[str] = []
    try:
        result = a / b
    except ZeroDivisionError:
        log.append("except")
        return None
    else:
        log.append("else")
        return result
    finally:
        log.append("finally")


# --- context manager（類別） ---
class Lock:
    def __init__(self) -> None:
        self.locked = False

    def __enter__(self) -> Lock:
        self.locked = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.locked = False  # 即使出錯也解鎖


# --- contextlib generator context manager ---
@contextmanager
def temporary_value(container: dict[str, int], key: str, value: int) -> Iterator[None]:
    original = container.get(key)
    container[key] = value
    try:
        yield
    finally:
        if original is None:
            container.pop(key, None)
        else:
            container[key] = original


@contextmanager
def timer() -> Iterator[list[float]]:
    holder: list[float] = []
    start = time.perf_counter()
    try:
        yield holder
    finally:
        holder.append(time.perf_counter() - start)


# --- EAFP ---
def get_nested(data: Mapping[str, object], *keys: str) -> object | None:
    """EAFP 巢狀存取。"""
    try:
        result: object = data
        for key in keys:
            result = result[key]  # type: ignore[index]
        return result
    except (KeyError, TypeError):
        return None


# --- suppress ---
def remove_key(d: dict[str, int], key: str) -> dict[str, int]:
    with suppress(KeyError):
        del d[key]
    return d
