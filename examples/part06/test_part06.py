"""Part 6 範例的驗證測試。

執行：pytest examples/part06
"""

import json

import pytest

from examples.part06.error_handling import (
    AccountNotFoundError,
    Bank,
    BankError,
    ConfigError,
    InsufficientFundsError,
    Lock,
    get_nested,
    load_config,
    remove_key,
    safe_divide,
    temporary_value,
    timer,
)


def test_custom_exception_hierarchy() -> None:
    bank = Bank()
    # 具體例外可被基底 BankError 接住
    with pytest.raises(BankError):
        bank.withdraw(99, 10)
    with pytest.raises(AccountNotFoundError) as exc_info:
        bank.withdraw(99, 10)
    assert exc_info.value.account_id == 99


def test_insufficient_funds_carries_data() -> None:
    bank = Bank()
    with pytest.raises(InsufficientFundsError) as exc_info:
        bank.withdraw(1, 1000)
    assert exc_info.value.shortfall == 900.0


def test_exception_chaining_preserves_cause() -> None:
    with pytest.raises(ConfigError) as exc_info:
        load_config("{not json}")
    assert isinstance(exc_info.value.__cause__, json.JSONDecodeError)


def test_try_except_else_finally() -> None:
    assert safe_divide(10, 2) == 5.0
    assert safe_divide(10, 0) is None


def test_context_manager_always_unlocks() -> None:
    lock = Lock()
    with pytest.raises(RuntimeError), lock:
        assert lock.locked is True
        raise RuntimeError("boom")
    assert lock.locked is False  # 即使出錯也解鎖


def test_temporary_value_restores() -> None:
    config = {"mode": 1}
    with temporary_value(config, "mode", 99):
        assert config["mode"] == 99
    assert config["mode"] == 1  # 還原

    # 原本不存在的 key，離開後移除
    with temporary_value(config, "new", 5):
        assert config["new"] == 5
    assert "new" not in config


def test_timer_records_even_on_error() -> None:
    holder: list[float]
    with pytest.raises(ValueError), timer() as holder:
        raise ValueError("boom")
    assert len(holder) == 1  # finally 記錄了耗時
    assert holder[0] >= 0


def test_eafp_nested_access() -> None:
    data = {"a": {"b": {"c": 42}}}
    assert get_nested(data, "a", "b", "c") == 42
    assert get_nested(data, "a", "x", "c") is None


def test_suppress_ignores_keyerror() -> None:
    assert remove_key({"a": 1}, "missing") == {"a": 1}
    assert remove_key({"a": 1}, "a") == {}
