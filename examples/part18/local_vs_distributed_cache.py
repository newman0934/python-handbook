"""Part 18 ch04:本地(行程內)快取在「多實例」下的一致性陷阱。

對應章節:chapters/18-performance/04-caching.md（延伸:本地 vs 分散式快取）

重點:`lru_cache` 是**行程內**的——每個行程/Pod 各有一份。資料更新時你只清得掉
「自己這台」,其他實例照樣回舊值。這正是「什麼時候不能用本地快取」的核心判準。
分散式快取(Redis/Memcached)把快取放在共享的外部服務,清一次全體生效。
"""

from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache

# 共用的資料源(模擬資料庫)
DB: dict[str, int] = {"price": 100}


def make_instance() -> Callable[[], int]:
    """模擬「一台伺服器實例」:它擁有自己獨立的一份行程內快取。"""

    @lru_cache(maxsize=32)
    def get_price() -> int:
        return DB["price"]  # 真的去查 DB

    return get_price


def demo() -> None:
    a = make_instance()  # 實例 A（Pod A）
    b = make_instance()  # 實例 B（Pod B）

    print("初始       A:", a(), " B:", b())
    DB["price"] = 200  # 資料更新了
    a.cache_clear()  # type: ignore[attr-defined]  # 只清得到「自己這台」
    print("A 清快取後 A:", a(), " B:", b(), "  ← B 還在回舊值!")


if __name__ == "__main__":
    demo()
