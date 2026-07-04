# Part 17 面試題:資料處理與科學計算

> 對應 [Part 17 資料處理](../chapters/17-data-science/README.md)。資料/後端職位常問——numpy 向量化、pandas loc/iloc、split-apply-combine、資料清理、polars。

---

## Q1.(必考)numpy 的 ndarray 為什麼比 Python list 快?

**考點**:numpy 基礎([01-numpy-basics](../chapters/17-data-science/01-numpy-basics.md))

**答**:

- **list**:一堆**散落的 Python 物件指標**——每個元素是完整物件(有拆箱/裝箱開銷),記憶體不連續(快取不友善)。
- **ndarray**:**同質固定型別 + 連續記憶體**——無拆箱裝箱、快取友善、可 SIMD,運算**下沉到 C 的向量化**。

```python
np.array([1,2,3]) * 2    # 整個陣列在 C 層一次算完(快)
[x*2 for x in [1,2,3]]   # Python 迴圈,每次拆箱/裝箱(慢)
```

**追問**:

- **shape/strides/dtype 的角色?** → shape(各維大小)、strides(各維跨幾 byte)、dtype(元素型別)。**reshape 和切片不複製資料**——只換「詮釋資訊」(strides)。
- **切片回傳 view 還是 copy?** → **view**(共享底層資料)!改 view 會改原陣列,要獨立用 `.copy()`。ndarray 是整個資料生態(pandas、ML)的底層。

---

## Q2. 什麼是向量化?廣播規則是什麼?

**考點**:向量化([02-numpy-vectorization](../chapters/17-data-science/02-numpy-vectorization.md))

**答**:**向量化**——以整體陣列運算取代 Python 迴圈,迴圈**下沉到 C 的 ufunc**(無直譯開銷、無拆箱、快取友善、SIMD)。

**廣播(broadcasting)規則**:兩陣列運算時,**末維右對齊**,逐維要求「**相等或其一為 1**」,靠 stride=0 **零複製**延展:

```python
a = np.ones((3, 4))     # (3, 4)
b = np.array([1,2,3,4]) # (4,)   → 右對齊,延展成 (3, 4)
a + b                    # OK
```

**追問**:`(n,)` vs `(n,1)` 的廣播方向不同(用 `reshape`/`None` 控制);`axis` 是**被消掉的維度**(`sum(axis=0)` 消掉列、逐欄加);布林遮罩、`np.where` 是向量化條件的標準做法;pandas 的欄運算底層都是這套。

---

## Q3.(必考)`loc` 和 `iloc` 差在哪?什麼是 index 對齊?

**考點**:pandas 基礎([03-pandas-basics](../chapters/17-data-science/03-pandas-basics.md))

**答**:

- **`loc`**:用**標籤**(label)選取(`df.loc["Alice", "age"]`)。
- **`iloc`**:用**位置**(integer position)選取(`df.iloc[0, 1]`)。

當 index 不是 0,1,2... 時兩者會不同。

**index 對齊**:pandas 運算**按標籤對齊**——兩個 Series 相加時,按 index 配對,**對不上的產生 NaN**(是威力也是坑):

```python
a = pd.Series([1,2], index=["x","y"])
b = pd.Series([10,20], index=["y","z"])
a + b    # x=NaN, y=22, z=NaN(按標籤對齊)
```

**追問**:

- **`SettingWithCopyWarning`?** → 鏈式索引(`df[df.a>0]["b"] = 1`)造成——不確定改到 view 還 copy。正解:`df.loc[df.a>0, "b"] = 1`(一次定位)。
- **`apply` 慢?** → `apply` 是逐元素 Python 迴圈,**優先向量化**(底層 numpy)。DataFrame = 多個共享同 index 的 Series。

---

## Q4. `groupby` 的 split-apply-combine?pandas merge 對應 SQL JOIN?

**考點**:DataFrame 操作([04-dataframe-operations](../chapters/17-data-science/04-dataframe-operations.md))

**答**:**split-apply-combine**:按鍵**拆分**→ 對每組**套用**聚合 →**合併**結果。內建聚合(`sum`/`mean`)走 **Cython 快路徑**,`apply(python_func)` 較慢。

**merge = SQL JOIN**:`how` 的 inner/left/right/outer 語意相同;**鍵重複會造成列數暴增**(同 [SQL JOIN 灌水](part23-data-analysis.md#q3-tuple-是不可變的),見 Part 23)。

```python
df.groupby("dept")["salary"].mean()          # split-apply-combine
df1.merge(df2, on="id", how="left")           # LEFT JOIN
```

**追問**:多欄 groupby 產生 **MultiIndex**(用 `reset_index`/`unstack` 重塑);`pivot_table` = groupby + unstack;取前 N 用 `nlargest`(比全排序快)。

---

## Q5. 資料清理的正確流程?缺失值怎麼處理?

**考點**:資料清理([05-data-cleaning](../chapters/17-data-science/05-data-cleaning.md))

**答**:正確順序:**體檢 → 轉型(coerce 把爛值變 NaN)→ 字串正規化 → 去重 → 填補/刪除**。

缺失值(NaN/None/pd.NA)有**傳染性**(NaN 參與運算/比較都是 NaN/False),偵測要用 **`isna()`**(不能 `== NaN`)。`pd.to_numeric(s, errors="coerce")` 把轉不動的值統一成 NaN 再處理。

**追問**:

- **填補策略取捨?** → drop(資料夠多)vs fill;平均(對稱)vs 中位數(偏態,見 [Part 24](part24-business-analytics.md#q1必考描述統計mean-和-median-什麼時候看哪個))vs ffill(時序)。
- **去重前先正規化字串**(否則 `North`/`north` 算兩個);`category` 型別省記憶體;整數欄遇缺失會升 float(或用 `Int64`)。

---

## Q6. Jupyter notebook 有什麼隱藏陷阱?

**考點**:Jupyter([07-jupyter](../chapters/17-data-science/07-jupyter.md))

**答**:**隱藏狀態 / 亂序執行**——kernel 是**持續存活、有狀態**的行程,變數跨 cell 保留。若你**亂序執行 cell**(或改了上面卻沒重跑),notebook 的狀態就**不可重現**(別人重跑會得不同結果,甚至你自己也是)。

**解法**:**Restart & Run All**——重啟 kernel 從頭跑,驗證真的可重現。執行計數 `In [n]` 顯示執行順序(可察覺亂序)。

**追問**:可重現實務——固定 seed、線性邏輯、清輸出再版控、重活抽成 `.py` 模組;magic(`%timeit`/`%%time`);**notebook 適合探索/報告,不適合放正式產品邏輯**(該進可測試的 `.py`)。

---

## Q7.(必考)為什麼機器學習要 train/test split?什麼是資料洩漏?

**考點**:ML 入門([08-machine-learning-intro](../chapters/17-data-science/08-machine-learning-intro.md))

**答**:監督式流程:準備 X/y → **train/test split** → fit → predict → 用**測試集**評估。

**為何 split**:要衡量模型對**新資料**的真實表現(泛化),不能用訓練資料評估——那樣模型「背答案」也能 100%(過擬合)。

**資料洩漏(隱蔽陷阱)**:測試集資訊洩漏進訓練——最經典是**在切分前做前處理**(標準化算了整份資料的統計)、或用未來資訊。用 **Pipeline** 防護(前處理綁進交叉驗證的每折)。

**追問**:過擬合(訓練好測試差,加資料/限制複雜度)vs 欠擬合(都差,加強模型/特徵);scikit-learn 的一致 API(fit/predict);**不平衡資料別只看準確率**(見 [Part 25](part25-machine-learning.md))。深入見 [Part 25](part25-machine-learning.md)。

---

## Q8. polars 和 pandas 差在哪?eager 和 lazy 求值?

**考點**:polars([09-polars](../chapters/17-data-science/09-polars.md))

**答**:polars 相對 pandas 的優勢:**多核平行(Rust,無 GIL)、Arrow 列式記憶體高效、惰性求值可全域優化**。

**eager vs lazy**:

- **eager**:每步**立刻執行**(pandas 就是這樣)。
- **lazy**:先**建查詢計畫**,執行前**全域優化**(謂詞下推/投影下推——只讀需要的欄/列),再執行:

```python
pl.scan_parquet("big.parquet")   # lazy,不立刻讀
  .filter(pl.col("x") > 0)
  .select(["x", "y"])
  .collect()                      # 執行時才優化 + 讀(只讀需要的)
```

**追問**:「看到整條查詢才能全域優化」(同資料庫查詢優化器),省 I/O/記憶體;**選型**:大資料/效能用 polars、小資料/既有生態用 pandas,可互通漸進採用。

---

⬅️ [Part 16](part16-architecture.md) ｜ [索引](README.md) ｜ ➡️ [Part 18 效能優化](part18-performance.md)
