"""Part 14 ch25 測試:SSE 格式與串流產生器。"""

from __future__ import annotations

import asyncio

from examples.part14.streaming_sse import collect, sse_format, token_stream


def test_sse_basic_format_ends_with_blank_line() -> None:
    assert sse_format("hello") == "data: hello\n\n"


def test_sse_with_event_and_id() -> None:
    assert sse_format("hi", event="token", id="1") == "event: token\nid: 1\ndata: hi\n\n"


def test_sse_multiline_data_prefixes_each_line() -> None:
    # 多行 data:每一行都要有 data: 前綴,才符合 SSE 規範
    assert sse_format("a\nb") == "data: a\ndata: b\n\n"


def test_token_stream_yields_events_then_done() -> None:
    chunks = asyncio.run(collect(token_stream(["Hel", "lo"])))
    assert len(chunks) == 3  # 2 個 token + 1 個 done
    assert "event: token" in chunks[0] and "data: Hel" in chunks[0]
    assert chunks[0].startswith("event: token\nid: 0\n")
    assert "event: done" in chunks[-1]
    assert chunks[-1].endswith("\n\n")  # 每筆都以空行收尾


def test_empty_stream_still_sends_done() -> None:
    chunks = asyncio.run(collect(token_stream([])))
    assert len(chunks) == 1
    assert "event: done" in chunks[0]
