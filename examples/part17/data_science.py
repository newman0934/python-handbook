"""Part 17 資料處理與科學計算範例：numpy 向量化 / pandas 操作 / 清理 / 視覺化。

以純函式封裝可驗證的行為，`test_part17.py` 以 pytest 驗證。
視覺化以 matplotlib 的 Agg 後端存檔（不需顯示器）。
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # 非互動後端：不開視窗、可存檔（須在 import pyplot 前）

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


# --- numpy：向量化與廣播（見 01, 02）---
def scale_and_shift(data: list[float], factor: float, offset: float) -> list[float]:
    """向量化：對整個陣列一次做 x * factor + offset。"""
    arr = np.asarray(data, dtype=np.float64)
    result = arr * factor + offset
    return [float(x) for x in result]


def broadcast_column_bonus(matrix: list[list[int]], bonus: list[int]) -> list[list[int]]:
    """廣播：(m,n) 矩陣的每一列加上不同的 bonus（bonus 形狀 (m,) → (m,1)）。"""
    m = np.asarray(matrix, dtype=np.int64)
    col = np.asarray(bonus, dtype=np.int64).reshape(-1, 1)
    result = m + col
    return [[int(v) for v in row] for row in result]


def pass_rate(scores: list[int], threshold: int) -> float:
    """布林遮罩：計算 >= threshold 的比率。"""
    arr = np.asarray(scores, dtype=np.int64)
    mask = arr >= threshold
    return float(mask.mean())


# --- pandas：groupby / merge（見 03, 04）---
def revenue_by_city(orders: list[dict[str, object]]) -> dict[str, int]:
    """split-apply-combine：依 city 分組加總 amount。"""
    df = pd.DataFrame(orders)
    grouped = df.groupby("city")["amount"].sum()
    return {str(city): int(total) for city, total in grouped.items()}


def revenue_by_country(
    orders: list[dict[str, object]], city_country: dict[str, str]
) -> dict[str, int]:
    """merge 補國家欄後，再依 country 分組加總。"""
    df = pd.DataFrame(orders)
    cities = pd.DataFrame({"city": list(city_country), "country": list(city_country.values())})
    merged = df.merge(cities, on="city", how="left")
    grouped = merged.groupby("country")["amount"].sum()
    return {str(country): int(total) for country, total in grouped.items()}


# --- pandas：資料清理（見 05）---
def clean_people(rows: list[dict[str, object]]) -> pd.DataFrame:
    """清理流程：型別轉換(coerce) → 中位數填補 → 字串正規化 → 去重。"""
    df = pd.DataFrame(rows)
    # 型別轉換：無法轉的變 NaN
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    # 中位數填補
    df["age"] = df["age"].fillna(df["age"].median())
    # 字串正規化（去重前必做）
    df["name"] = df["name"].astype("string").str.strip()
    # 去重（依 name 保留第一筆）並重設 index
    df = df.drop_duplicates(subset="name", keep="first").reset_index(drop=True)
    return df


# --- 視覺化（見 06）---
def save_bar_chart(labels: list[str], values: list[float], path: Path) -> bool:
    """畫長條圖並存檔（Agg 後端，無需顯示器）。回傳檔案是否成功產生。"""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(labels, values, color="tab:green")
    ax.set_title("Bar Chart")
    fig.tight_layout()
    fig.savefig(path, dpi=80)
    plt.close(fig)  # 釋放記憶體
    return path.exists() and path.stat().st_size > 0
