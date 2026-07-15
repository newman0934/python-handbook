"""Part 14 ch24:FastAPI lifespan 的核心模式(可執行、可測)。

對應章節:chapters/14-web/24-lifespan-startup.md

lifespan 就是一個 async context manager:
  startup(yield 之前)取得資源 → 應用服務期間 → shutdown(yield 之後)保證釋放。
真實的 FastAPI 寫法是 FastAPI(lifespan=lifespan);這裡把「取得→服務→保證清理」
的骨架抽出來,用 asyncio.run 就能驗證(不需啟動伺服器)。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass


@dataclass
class FakePool:
    """模擬一個要「開機取得、關機釋放」的資源(如 DB 連線池)。"""

    opened: bool = False
    closed: bool = False

    def open(self) -> None:
        self.opened = True

    def close(self) -> None:
        self.closed = True


@dataclass
class AppState:
    """放跨請求共用的資源(對應 FastAPI 的 app.state)。"""

    pool: FakePool | None = None


@asynccontextmanager
async def lifespan(state: AppState) -> AsyncIterator[None]:
    """開機取得資源、關機保證釋放——即使服務期間拋例外也會清理。"""
    pool = FakePool()
    pool.open()  # startup:初始化連線池 / Redis / HTTP client / 模型
    state.pool = pool
    try:
        yield  # 應用在此服務請求
    finally:
        pool.close()  # shutdown:釋放資源(finally 保證一定跑到)


async def run_normal() -> AppState:
    state = AppState()
    async with lifespan(state):
        pass  # 服務期間
    return state


async def run_with_error() -> AppState:
    state = AppState()
    try:
        async with lifespan(state):
            raise RuntimeError("請求處理期間炸了")
    except RuntimeError:
        pass
    return state


async def demo() -> None:
    state = AppState()
    async with lifespan(state):
        assert state.pool is not None
        print("服務中: opened =", state.pool.opened, "closed =", state.pool.closed)
    print("關機後: closed =", state.pool.closed)


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo())
