"""Part 11 範例的驗證測試。

執行：pytest examples/part11
"""

from datetime import UTC, datetime

from examples.part11.stdlib import (
    Playlist,
    describe_capabilities,
    encode_with_datetime,
    extract_dates,
    is_aware,
    json_roundtrip,
    normalize_whitespace,
    now_utc_is_aware,
    parse_csv,
    parse_toml,
    path_parts,
    total,
    utc_to_taipei,
    write_and_count_lines,
)


def test_path_parts() -> None:
    assert path_parts("/home/user/report.tar.gz") == {
        "name": "report.tar.gz",
        "stem": "report.tar",
        "suffix": ".gz",
        "parent": "/home/user",
    }


def test_datetime_aware_and_timezone() -> None:
    utc = datetime(2026, 7, 2, 7, 30, tzinfo=UTC)
    assert is_aware(utc)
    assert not is_aware(datetime(2026, 7, 2, 7, 30))  # naive
    taipei = utc_to_taipei(utc)
    assert taipei.hour == 15  # UTC+8
    assert now_utc_is_aware()


def test_json_tuple_becomes_list() -> None:
    # tuple 序列化後讀回變 list
    assert json_roundtrip({"p": (1, 2)}) == {"p": [1, 2]}


def test_json_datetime_encoding() -> None:
    result = encode_with_datetime({"time": datetime(2026, 7, 2, 15, 30)})
    assert "2026-07-02T15:30:00" in result


def test_re_extract_dates() -> None:
    assert extract_dates("會議 2026-07-02，截止 2026-08-15") == [
        "2026-07-02",
        "2026-08-15",
    ]


def test_re_normalize_whitespace() -> None:
    assert normalize_whitespace("多個    空白  ") == "多個 空白"


def test_csv_handles_quoted_comma() -> None:
    rows = parse_csv('name,note\nAlice,"Smith, John"\nBob,plain')
    assert rows[0]["note"] == "Smith, John"  # 引號內逗號正確保留
    assert rows[1]["note"] == "plain"


def test_toml_has_types() -> None:
    config = parse_toml('[server]\nhost = "localhost"\nport = 8080\ndebug = true')
    server = config["server"]
    assert isinstance(server, dict)
    assert server["port"] == 8080  # int
    assert server["debug"] is True  # bool


def test_collections_abc_total() -> None:
    assert total([1, 2, 3]) == 6
    assert total((1, 2, 3)) == 6  # tuple 也可迭代
    assert total(x for x in range(4)) == 6  # 生成器


def test_capabilities() -> None:
    assert describe_capabilities([1, 2]) == ["iterable", "sequence"]
    assert describe_capabilities({1: 2}) == ["iterable"]
    assert describe_capabilities(42) == []


def test_playlist_sequence_mixins() -> None:
    pl = Playlist(["a", "b", "c"])
    assert len(pl) == 3
    assert "b" in pl  # 來自 Sequence 混入
    assert pl.index("b") == 1  # 來自 Sequence 混入
    assert list(reversed(pl)) == ["c", "b", "a"]


def test_tempfile_and_io() -> None:
    assert write_and_count_lines("第一行\n第二行\n第三行\n") == 3
