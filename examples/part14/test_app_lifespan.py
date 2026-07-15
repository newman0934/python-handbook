"""Part 14 ch24 測試:lifespan 的取得與保證釋放。"""

from __future__ import annotations

import asyncio

from examples.part14.app_lifespan import AppState, lifespan, run_normal, run_with_error


def test_resource_open_during_and_closed_after() -> None:
    async def scenario() -> None:
        state = AppState()
        async with lifespan(state):
            assert state.pool is not None
            assert state.pool.opened is True
            assert state.pool.closed is False  # 服務期間還開著
        assert state.pool.closed is True  # 關機後釋放

    asyncio.run(scenario())


def test_normal_lifecycle_closes() -> None:
    state = asyncio.run(run_normal())
    assert state.pool is not None
    assert state.pool.opened is True
    assert state.pool.closed is True


def test_cleanup_runs_even_on_error() -> None:
    # 服務期間拋例外,shutdown 仍要清理(finally 保證)
    state = asyncio.run(run_with_error())
    assert state.pool is not None
    assert state.pool.closed is True
