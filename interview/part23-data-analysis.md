# Part 23 面試題:分析用 SQL 與資料整理

> 對應 [Part 23 分析用 SQL 與資料整理](../chapters/23-data-analysis/README.md)。**Data Analyst 核心**——SQL 聚合/JOIN/window、pandas 整理、EDA。

---

## Q1. 資料分析師的工作流是什麼?為什麼「清理」最花時間?

**考點**:工作流([01-analyst-workflow](../chapters/23-data-analysis/01-analyst-workflow.md))

**答**:**定義問題 → 取得 → 清理 → 探索 → 分析 → 溝通**,且是**迭代循環**(探索發現問題就回頭)。

**清理最花時間(60-80%)**:真實資料是**業務系統運作的副產物**(不是為分析而生)——充滿缺值、重複、格式不一、髒值。而**所有結論都建立在資料品質上**(garbage in garbage out),所以清理是保證結論正確的前提,不是雜活。

**追問**:「**問對問題**」最重要(定義錯了再好的分析都沒用);分析師 vs 資料科學家 vs 資料工程師(回答商業問題 vs 建模預測 vs 建管線);核心技能:**SQL + 統計 + 溝通**。

---

## Q2.(必考)`WHERE` 和 `HAVING` 差在哪?查詢的執行順序?

**考點**:SQL 聚合([02-sql-aggregation](../chapters/23-data-analysis/02-sql-aggregation.md))

**答**:

- **`WHERE`**:**分組前**過濾**列**(不能用聚合函式)。
- **`HAVING`**:**分組後**過濾**組**(可用聚合函式)。

對應**邏輯執行順序**:`FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`——`WHERE` 在 GROUP BY 前(那時還沒有聚合值)、`HAVING` 在後。

```sql
SELECT region, SUM(amount) FROM sales
WHERE amount > 0          -- 篩列(分組前)
GROUP BY region
HAVING SUM(amount) > 1000 -- 篩組(分組後)
```

**追問**:聚合與 NULL——`AVG`/`COUNT(col)` **忽略 NULL**、`COUNT(*)` 不忽略(分母要清楚);在資料庫端聚合(只傳小結果集,別整批撈回本機)。

---

## Q3.(必考)INNER 和 LEFT JOIN 差在哪?什麼是 JOIN 灌水?

**考點**:JOIN([03-sql-joins](../chapters/23-data-analysis/03-sql-joins.md))

**答**:

- **INNER JOIN**:只留**兩表都匹配**的列(沒訂單的客戶消失)。
- **LEFT JOIN**:保留**左表全部**,右表無匹配補 NULL。

要「所有客戶」用 LEFT、要「有訂單的客戶」用 INNER——**選錯會默默漏資料**。

**JOIN 灌水(fan-out)**:一對多 JOIN 會**複製左列**,若接著聚合會**重複計算**(總和變倍數)。**不報錯、結果照跑,最難查**:

```sql
-- 一個客戶 3 訂單 × 2 標籤 → 訂單被複製成 6 列 → SUM 灌成 2 倍!
```

防範:別把兩個一對多 JOIN 在一起聚合,用**子查詢/CTE 先各自聚合**、或 `COUNT(DISTINCT)`。

**追問**:JOIN 的**粒度**(JOIN 後「一列代表什麼」,聚合前必確認);LEFT JOIN 後 `COUNT(fk)` 得 0、`COALESCE(SUM, 0)` 補 NULL。

---

## Q4.(必考)window function 和 GROUP BY 差在哪?怎麼做 Top-N per group?

**考點**:window functions([04-sql-window-functions](../chapters/23-data-analysis/04-sql-window-functions.md))

**答**:

- **GROUP BY**:**壓縮**列(N 列 → 每組一列,明細消失)。
- **window function**:**不壓縮**(N 進 N 出,每列附上「群體視角」如排名/佔比)。

```sql
RANK() OVER (PARTITION BY region ORDER BY amount DESC)   -- 各區排名,每列都保留
amount - LAG(amount) OVER (PARTITION BY region ORDER BY month)  -- 環比
SUM(amount) OVER ()   -- 佔全體比例
```

**Top-N per group**:因為 **`WHERE` 不能直接用 window**(window 在 SELECT 階段才算),要用 **CTE 包住排名,外層 `WHERE rnk <= N`**:

```sql
WITH ranked AS (
  SELECT *, RANK() OVER (PARTITION BY region ORDER BY sales DESC) AS rnk FROM t
)
SELECT * FROM ranked WHERE rnk <= 3;   -- 每區前 3
```

**追問**:ROW_NUMBER(唯一序號)/RANK(並列跳號)/DENSE_RANK(並列不跳);視窗三要素 PARTITION BY / ORDER BY / 框架(ROWS BETWEEN)。

---

## Q5. CTE 有什麼好處?和子查詢差在哪?

**考點**:CTE([05-sql-cte-pivot](../chapters/23-data-analysis/05-sql-cte-pivot.md))

**答**:CTE(`WITH`)把複雜查詢拆成**具名的中間步驟**——由上而下閱讀、可複用、好除錯,勝過深層巢狀子查詢:

```sql
WITH region_totals AS (SELECT region, SUM(amount) AS total FROM sales GROUP BY region)
SELECT region, total, ROUND(100.0*total/(SELECT SUM(total) FROM region_totals), 1) AS pct
FROM region_totals;
```

**CTE vs 子查詢**:功能相近,但 **CTE 可讀性遠勝**;純量子查詢適合「與整體比較」(高於平均)。CTE 是**具名子查詢**(非實體表,優化器多會內聯)。

**追問**:CASE 樞紐(`SUM(CASE WHEN product='A' THEN amount ELSE 0 END)`)長轉寬,但**欄位要固定**(動態欄用 [pandas pivot](#q7-pandas-的-merge-對應-sql-join嗎long-和-wide-格式怎麼選));相關子查詢對每列各跑一次(效能差)。

---

## Q6. pandas groupby 的心智模型?`agg` 和 `transform` 差在哪?

**考點**:pandas groupby([06-pandas-groupby](../chapters/23-data-analysis/06-pandas-groupby.md))

**答**:**split-apply-combine**:拆分(按鍵)→ 套用(聚合/轉換/過濾)→ 合併。

- **`agg`**:**壓縮**成摘要(對應 SQL GROUP BY)。
- **`transform`**:**保形**——回傳與原表等長,貼回原位(對應 SQL window,如算佔比):

```python
df.groupby("region").agg(total=("amount", "sum"))       # 壓縮:每區一列
df.groupby("region")["amount"].transform("sum")          # 保形:每列貼上所屬區總額
```

**追問**:named aggregation(`agg(name=(col, func))`);聚合後 `reset_index()`(分組鍵從索引變回欄);聚合**跳過 NaN**(分母意識);SQL↔pandas 對照(GROUP BY→groupby、window→transform、HAVING→filter)。

---

## Q7. pandas 的 merge 對應 SQL JOIN 嗎?long 和 wide 格式怎麼選?

**考點**:merge/reshape([07-merge-reshape](../chapters/23-data-analysis/07-merge-reshape.md))

**答**:`merge` 的 `how=inner/left/outer` 對應 SQL JOIN,**連灌水陷阱都一樣**。但 pandas 有 SQL 沒有的**防呆**:`validate="one_to_many"`(關係不符就報錯)、`indicator=True`(加 `_merge` 欄看匹配狀況)。

**long vs wide**:

- **long(tidy)**:每變數一欄、每觀測一列——**分析用**(groupby/畫圖/ML 都預期這形狀)。
- **wide(交叉表)**:類別展開成欄——**呈現用**(人看報表方便)。

`pivot_table`(長→寬,能聚合、動態產生欄)和 `melt`(寬→長)互逆。**進來的寬報表先 melt 分析,輸出報表再 pivot**。

**追問**:pandas 樞紐勝過 [SQL CASE](#q5-cte-有什麼好處和子查詢差在哪)(動態欄不必手列);鍵型別要一致(int 對 str 不匹配)。

---

## Q8. EDA 要看什麼?為什麼用 IQR 抓離群?

**考點**:EDA([08-eda](../chapters/23-data-analysis/08-eda.md))

**答**:EDA 目的:**認識資料、發現品質問題、形成假設、選對後續方法**。檢查維度:**規模結構 → 缺值 → 單變量(數值 describe / 類別 value_counts)→ 離群 → 雙變量關係(相關)**。

**IQR 抓離群為何穩健**:不能用「平均 ± N 倍標準差」——**離群值本身會拉高平均和標準差**,反而抓不到。**IQR 用四分位數(Q1/Q3),不被極端值污染**:

```text
離群 = 值 < Q1 − 1.5×IQR 或 值 > Q3 + 1.5×IQR
```

**追問**:解讀 describe——**mean vs median 判偏態**(見 [Part 24](part24-business-analytics.md#q1必考描述統計mean-和-median-什麼時候看哪個))、std/max 判離散與離群、count 判缺值;**離群不等於錯誤**(真實極端值要留,靠領域判斷)。

---

## Q9. 端到端分析怎麼分工 SQL 和 pandas?

**考點**:Capstone([09-capstone-analysis](../chapters/23-data-analysis/09-capstone-analysis.md))

**答**:**SQL 做重活、pandas 做細活**:

- **SQL**:資料庫端 JOIN + 聚合 + window(利用索引/優化器,**只撈回聚合結果**,省傳輸與記憶體)。
- **pandas**:撈回後的靈活整理——樞紐、衍生欄(佔比)、EDA、視覺化。
- **銜接點**:`pd.read_sql_query(sql, conn)`。

**追問**:別把原始大表整批撈回本機(該在 SQL 端聚合減量);**JOIN 決定結果範圍**(INNER 排除無匹配者,報告要說明限制、必要時用 LEFT);趨勢用 pivot、成長率用 window。

---

⬅️ [Part 22](part22-distributed-systems.md) ｜ [索引](README.md) ｜ ➡️ [Part 24 統計分析與商業洞察](part24-business-analytics.md)
