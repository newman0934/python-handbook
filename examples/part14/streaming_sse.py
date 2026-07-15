"""Part 14 ch25:串流回應與 Server-Sent Events(SSE)核心。

對應章節:chapters/14-web/25-streaming-sse.md

兩個可測核心:
- sse_format:把一筆資料組成 SSE 線路格式(`event:`/`id:`/`data:` + 空行結尾)。
- token_stream:一個 async 產生器,逐筆 yield SSE 事件(模擬 LLM 逐字輸出)。
真實 FastAPI 用 StreamingResponse(gen, media_type="text/event-stream") 把產生器接出去,
瀏覽器用 EventSource 收;這裡把產生器與格式抽出來,用 asyncio 就能驗證。
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator


def sse_format(data: str, event: str | None = None, id: str | None = None) -> str:
    """組一筆 SSE 事件:選填 event/id,data 逐行加前綴,整筆以空行結尾。"""
    lines: list[str] = []
    if event is not None:
        lines.append(f"event: {event}")
    if id is not None:
        lines.append(f"id: {id}")
    for part in data.split("\n"):  # 多行 data 每行都要 data: 前綴
        lines.append(f"data: {part}")
    return "\n".join(lines) + "\n\n"  # 空行(\n\n)代表一筆事件結束


async def token_stream(tokens: list[str]) -> AsyncIterator[str]:
    """模擬 LLM 逐字輸出:一個一個 yield SSE 事件,最後送 done。"""
    for i, tok in enumerate(tokens):
        yield sse_format(tok, event="token", id=str(i))
        await asyncio.sleep(0)  # 讓出控制權(真實情境是等模型產下一個 token)
    yield sse_format("[DONE]", event="done")


async def collect(gen: AsyncIterator[str]) -> list[str]:
    return [chunk async for chunk in gen]


def demo() -> None:
    print(repr(sse_format("hello")))
    print(repr(sse_format("hi", event="token", id="1")))
    chunks = asyncio.run(collect(token_stream(["Hel", "lo"])))
    print("串流事件數:", len(chunks))


if __name__ == "__main__":
    demo()
