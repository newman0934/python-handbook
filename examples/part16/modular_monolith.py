"""Part 16 ch12:模組化單體的「模組邊界」在程式上長什麼樣。

對應章節:chapters/16-architecture/12-modular-monolith.md

核心規則:模組之間只透過**公開介面**往來,不碰對方的內部(model / table / 私有類別)。
把邊界守住,「模組化單體 → 抽某模組成微服務」就只是換一個實作——業務碼一行不動。
這裡用 users 與 orders 兩個模組示範。
"""

from __future__ import annotations

from typing import Protocol


# ===== users 模組 =====
class UsersAPI(Protocol):
    """users 模組的公開介面——其他模組只能依賴這個。"""

    def get_user_name(self, user_id: int) -> str: ...


class _UserRow:
    """模組私有(前底線):內部怎麼存資料是 users 自己的事,外部不該 import。"""

    def __init__(self, uid: int, name: str) -> None:
        self.uid = uid
        self.name = name


class LocalUsers:
    """模組化單體:同行程直接呼叫(實作 UsersAPI)。"""

    def __init__(self) -> None:
        self._rows = {1: _UserRow(1, "Ada"), 2: _UserRow(2, "Bob")}

    def get_user_name(self, user_id: int) -> str:
        return self._rows[user_id].name


# ===== orders 模組 =====
class OrderService:
    """只依賴 UsersAPI,不碰 users 的內部(_UserRow / LocalUsers 都不 import)。"""

    def __init__(self, users: UsersAPI) -> None:
        self._users = users

    def place_order(self, user_id: int, item: str) -> str:
        name = self._users.get_user_name(user_id)  # 走公開介面
        return f"{name} 下單:{item}"


# ===== 演進:把 users 抽成微服務,orders 一行都不改 =====
class RemoteUsers:
    """同一個 UsersAPI,改成打遠端(模擬 HTTP)——這就是「抽成服務」的接縫。"""

    def __init__(self, directory: dict[int, str]) -> None:
        self._dir = directory

    def get_user_name(self, user_id: int) -> str:
        return self._dir[user_id]  # 真實世界:httpx.get(f".../users/{user_id}")


def demo() -> None:
    svc = OrderService(LocalUsers())
    print("單體內   :", svc.place_order(1, "書"))
    # 把 users 換成遠端實作,OrderService 完全沒改
    svc2 = OrderService(RemoteUsers({1: "Ada"}))
    print("抽成服務後:", svc2.place_order(1, "書"))


if __name__ == "__main__":
    demo()
