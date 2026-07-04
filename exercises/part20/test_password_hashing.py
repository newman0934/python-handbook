"""Part 20 password_hashing 測試。"""

from __future__ import annotations

from exercises.part20.password_hashing import hash_password, verify_password


def test_verify_correct_password() -> None:
    stored = hash_password("s3cret")
    assert verify_password("s3cret", stored) is True


def test_verify_wrong_password() -> None:
    stored = hash_password("s3cret")
    assert verify_password("wrong", stored) is False


def test_salt_makes_hashes_differ() -> None:
    # 同密碼兩次雜湊,因隨機 salt 而不同(但都能驗證通過)
    a = hash_password("same")
    b = hash_password("same")
    assert a != b
    assert verify_password("same", a)
    assert verify_password("same", b)
