"""Part 17 dataframe_ops 測試。"""

from __future__ import annotations

import pandas as pd

from exercises.part17.dataframe_ops import top_category, total_by_category


def _df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"category": "a", "amount": 10.0},
            {"category": "b", "amount": 5.0},
            {"category": "a", "amount": 20.0},
        ]
    )


def test_total_by_category() -> None:
    assert total_by_category(_df()) == {"a": 30.0, "b": 5.0}


def test_top_category() -> None:
    assert top_category(_df()) == "a"
