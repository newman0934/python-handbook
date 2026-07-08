# 向量資料庫 (pgvector / Chroma / FAISS)

> [語意搜尋](06-embeddings-semantic-search.md)要對「查詢向量」找「最相似的文件向量」。文件一多(幾百萬筆),線性比對每一個就太慢了。**向量資料庫**專門儲存向量、並用**近似最近鄰(ANN)** 索引在毫秒內找出最相似的 top-k。這章講向量資料庫的角色、ANN 的原理,以及選型。

## 💡 白話導讀(建議先讀)

[上一章](06-embeddings-semantic-search.md)把文字變成了「語意地圖上的點」。
但真實應用有**幾百萬個點**,使用者一查詢,難道要**跟每一個點算距離**、
再排序?幾百萬次計算,太慢了。這章講怎麼**又快又準地找到最近鄰**。

先認清這是個取捨:

- **精確搜尋(暴力法)**:跟每個向量都比一次,**保證找到最準的**,但 **O(n)**——
  百萬筆就百萬次,慢到不能用。
- **近似最近鄰(ANN)**:用聰明的索引結構,**只檢查一小撮候選**,
  就找出「幾乎一定是最近的」那幾個。**犧牲一點點準確度,換來幾百倍速度**——
  這在實務上完全划算(搜尋結果第 8 名和第 9 名互換,沒人在乎)。

這就是**向量資料庫**的核心價值:它把 ANN 索引(如 **HNSW**——
一種像「多層跳表」的圖結構,還記得 [Redis 的跳表](../15-database/18-redis.md)嗎)
封裝成好用的服務,還幫你處理**過濾**(「只搜這個使用者的文件」)、
**持久化**、**擴展**。

工具選型這章會比較:輕量的 **FAISS/Chroma**(本機、原型夠用)、
生產級的 **pgvector**(直接長在你的 [PostgreSQL](../15-database/22-postgresql-features.md) 上,
一庫多用、省維運)、以及 **Pinecone/Weaviate/Qdrant** 等專用服務。
這章帶你用一個向量資料庫,把上一章的語意搜尋**規模化**到百萬級文件——
這正是把 RAG 從 demo 推向生產的關鍵一步。

## Why(為什麼)

[embedding](06-embeddings-semantic-search.md) 把知識庫每個片段轉成向量後,語意搜尋就是「找和查詢向量最相似的向量」。小規模(幾百個)時,線性掃過每一個算餘弦相似度就行。但真實知識庫有**幾十萬到幾千萬個向量**,每次查詢都線性比對全部——**O(n),太慢**(百萬向量 × 每次查詢 = 幾秒延遲,無法即時)。

而且你還需要:**持久化儲存**大量高維向量、**新增/刪除/更新**向量、把向量和**中繼資料**(原文、來源、時間)綁在一起、**過濾**(只在某類別內搜)。用一般資料庫硬存向量再自己算相似度,又慢又難維護。

**向量資料庫(vector database)** 專為此而生:

- **高效儲存**大量高維向量。
- **近似最近鄰(ANN)索引**:犧牲一點點精確度,換來**次線性**的查詢速度——百萬向量也能毫秒級找出 top-k。
- **中繼資料 + 過濾**:向量綁原文與屬性,可先過濾再搜。
- **CRUD**:新增/刪除/更新向量。

它是 [RAG](../29-ai-applications/README.md) 的檢索引擎——RAG 從向量資料庫語意檢索相關片段餵給 LLM。這章講它的原理與選型(pgvector、Chroma、FAISS、Pinecone…)。

## Theory(理論:精確 vs 近似最近鄰)

**最近鄰搜尋(nearest neighbor)**:給一個查詢向量,找資料庫中**最相似(最近)** 的向量。兩種:

- **精確最近鄰(exact / brute-force)**:算查詢和**每一個**向量的相似度,取最高的 k 個。**保證正確,但 O(n)**——n 大就慢。
- **近似最近鄰(Approximate Nearest Neighbor, ANN)**:用聰明的索引結構,**只檢查一小部分候選**就找出「幾乎一定是」最相似的 top-k。**次線性(如 O(log n))、極快,但可能偶爾漏掉真正最近的**(精確度略降,通常 95%+ 召回率)。**大規模語意搜尋幾乎都用 ANN**——為了速度,接受一點點不精確。

**ANN 的常見演算法**:

- **HNSW(Hierarchical Navigable Small World)**:建一個**多層圖**,高層稀疏、低層密集;查詢從高層粗略導航、逐層下降到精確鄰居。**快、高召回,最主流**(pgvector、Chroma、Qdrant 都用)。
- **IVF(Inverted File)**:把向量空間**分群**,查詢時只搜最近的幾個群。
- **PQ(Product Quantization)**:壓縮向量省記憶體(大規模用)。

**度量**:與 [embedding](06-embeddings-semantic-search.md) 一致——餘弦相似度(或正規化後的點積、歐氏距離)。

## Specification(規範:向量資料庫選型)

**常見選項**:

| 工具 | 定位 | 適用 |
|------|------|------|
| **pgvector** | PostgreSQL 的向量擴充 | 已用 Postgres、想在一個 DB 裡同時存關聯資料 + 向量(見 [SQLAlchemy](../15-database/README.md)) |
| **Chroma** | 輕量嵌入式向量庫 | 開發/原型、本地跑、小中規模 |
| **FAISS** | Meta 的向量檢索函式庫 | 極高效能、自建索引、可嵌入應用(非完整 DB) |
| **Qdrant / Weaviate / Milvus** | 專用向量資料庫 | 大規模、需過濾/分散式/雲託管 |
| **Pinecone** | 全託管向量資料庫 | 不想自管、要雲端擴展 |

**核心操作**(概念上一致):

```python
# 概念(各家 API 不同):
index.add(id, vector, metadata)          # 新增向量 + 中繼資料
results = index.search(query_vector, k=5, filter={"category": "docs"})  # 檢索 top-k(可過濾)
index.delete(id)                          # 刪除
```

**pgvector 範例**(SQL,見 [Part 15](../15-database/README.md)):

```sql
CREATE EXTENSION vector;
CREATE TABLE docs (id bigserial, content text, embedding vector(1536));
CREATE INDEX ON docs USING hnsw (embedding vector_cosine_ops);  -- HNSW 索引
-- 查詢:找和查詢向量最相似的 5 筆(<=> 是餘弦距離運算子)
SELECT content FROM docs ORDER BY embedding <=> '[...]' LIMIT 5;
```

**選型準則**:已用 Postgres → pgvector;原型/小規模 → Chroma;要極致效能/自控 → FAISS;大規模託管 → Pinecone/Qdrant。

## Implementation(底層:ANN 為何快、正規化加速)

**ANN 為何能次線性**:精確搜尋要比對全部 n 個向量。ANN 的索引(如 HNSW 的多層圖)讓查詢**只走訪一小部分向量**就逼近答案——像在圖上「導航」:從一個入口點出發,每步跳到「更接近查詢」的鄰居,少數幾步就到達目標區域,只算了 log n 級別的向量,而非全部。代價是**可能錯過真正最近的那個**(它不在你走過的路徑上),所以是「近似」。實務上調參數可在**速度 vs 召回率**間權衡(HNSW 的 `ef` 參數:搜更多候選 → 更準但更慢)。對語意搜尋,95%+ 的召回率通常足夠,而速度快幾個數量級——這個取捨划算。

**正規化 → 點積 = 餘弦,加速比較**:餘弦相似度要算 `(A·B)/(|A||B|)`,每次都要算兩個長度(norm)。若**預先把所有向量正規化成單位長度**(|v|=1),餘弦就簡化成**純點積 `A·B`**(分母都是 1)——省去 norm 計算。點積是高度優化的向量運算(見 [numpy 向量化](../17-data-science/02-numpy-vectorization.md)、BLAS),大量比較時快很多。所以向量資料庫通常存正規化後的向量、用點積(內積)當度量。

**中繼資料過濾的價值**:向量資料庫把向量和**中繼資料**(原文、類別、時間、來源)綁在一起,查詢時可**先過濾再搜**(「只在 2024 年的文件裡語意搜尋」)。這對 RAG 很重要——可依權限、時效、來源縮小範圍再檢索。下面範例用純 numpy 實作一個記憶體向量索引(正規化 + 點積 kNN 搜尋),展示核心原理(真實用 pgvector/Chroma/FAISS 的 ANN 索引)。

## Code Example(可執行的 Python 範例)

```python
# vector_index.py — 記憶體向量索引:正規化 + kNN 搜尋(需要 numpy)
from __future__ import annotations

import numpy as np


class VectorIndex:
    """簡易向量索引:存正規化向量 + 中繼資料,用點積(=餘弦)找 top-k。
    (真實用 pgvector/Chroma/FAISS 的 ANN 索引,可次線性搜百萬向量。)"""

    def __init__(self) -> None:
        self._ids: list[str] = []
        self._vectors: list[np.ndarray] = []
        self._metadata: list[dict[str, str]] = []

    @staticmethod
    def _normalize(vec: list[float]) -> np.ndarray:
        v = np.asarray(vec, dtype=np.float64)
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else v

    def add(self, doc_id: str, vector: list[float], metadata: dict[str, str]) -> None:
        self._ids.append(doc_id)
        self._vectors.append(self._normalize(vector))  # 存正規化向量
        self._metadata.append(metadata)

    def search(
        self, query: list[float], k: int = 3, category: str | None = None
    ) -> list[tuple[float, str, dict[str, str]]]:
        """kNN 檢索:正規化後點積=餘弦相似度。可先按 category 過濾。"""
        q = self._normalize(query)
        results: list[tuple[float, str, dict[str, str]]] = []
        for doc_id, vec, meta in zip(self._ids, self._vectors, self._metadata):
            if category is not None and meta.get("category") != category:
                continue  # 中繼資料過濾:先過濾再搜
            score = float(np.dot(q, vec))  # 正規化後點積 = 餘弦相似度
            results.append((score, doc_id, meta))
        results.sort(reverse=True, key=lambda r: r[0])
        return results[:k]


def main() -> None:
    index = VectorIndex()
    # 新增文件向量 + 中繼資料(真實向量由 embedding 模型產生)
    index.add("d1", [0.90, 0.10, 0.05], {"category": "程式", "text": "Python 是程式語言"})
    index.add("d2", [0.05, 0.10, 0.90], {"category": "動物", "text": "貓是可愛的動物"})
    index.add("d3", [0.70, 0.30, 0.10], {"category": "程式", "text": "Java 也是程式語言"})

    # 語意檢索:查詢接近「程式語言」
    print("語意檢索 top-2:")
    for score, doc_id, meta in index.search([0.88, 0.12, 0.05], k=2):
        print(f"  {score:.3f}  {doc_id}  {meta['text']}")

    # 中繼資料過濾:只在「動物」類別搜
    print("\n只在「動物」類別搜:")
    for score, doc_id, meta in index.search([0.88, 0.12, 0.05], k=3, category="動物"):
        print(f"  {score:.3f}  {doc_id}  {meta['text']}")


if __name__ == "__main__":
    main()
```

**預期輸出**:

```pycon
$ python vector_index.py
語意檢索 top-2:
  1.000  d1  Python 是程式語言
  0.962  d3  Java 也是程式語言

只在「動物」類別搜:
  0.125  d2  貓是可愛的動物
```

逐段解說:

- **`add` 存正規化向量**:每個向量存進去前先正規化成單位長度——這樣搜尋時點積直接等於餘弦相似度,省去每次算 norm。同時綁上**中繼資料**(category、原文)。
- **`search` 用點積**:查詢也正規化,和每個文件向量算**點積**(= 餘弦)、排序取 top-k。語意檢索找出 Python(1.000)、Java(0.962)——即使查詢沒提 Java,語意相近仍被找出。
- **中繼資料過濾**:`category="動物"` 時,只在動物類別搜——即使查詢語意偏「程式」,也只回動物類的結果(d2)。這是「先過濾再搜」,對 RAG 依權限/時效縮小範圍很有用。
- **真實的差異**:此範例是**線性掃描**(O(n),小規模可)。真實向量資料庫用 **ANN 索引(HNSW 等)** 達次線性,百萬向量也毫秒級——原理相同(找最相似向量),但索引結構讓它可擴展。
- **要點**:向量資料庫 = 存向量 + ANN 索引(快速找最相似)+ 中繼資料過濾。是語意搜尋/RAG 的檢索引擎。

## Diagram(圖解:向量資料庫在 RAG 的位置)

```mermaid
flowchart TD
    subgraph INGEST["建索引(離線)"]
        DOC["文件分塊"] -->|embedding 模型| VEC["向量"]
        VEC --> VDB[("向量資料庫<br/>ANN 索引 + 中繼資料")]
    end
    subgraph SEARCH["檢索(查詢時)"]
        Q["查詢"] -->|embedding| QV["查詢向量"]
        QV --> VDB
        VDB -->|ANN 找 top-k<br/>(可過濾)| TOPK["最相似片段"]
        TOPK --> LLM["餵給 LLM 回答<br/>(RAG,見 Part 29)"]
    end
    style VDB fill:#e3f2fd
    style TOPK fill:#e8f5e9
```

## Best Practice(最佳實踐)

- **大量向量用向量資料庫的 ANN 索引**:別線性掃全部(O(n) 慢)。
- **依情境選型**:已用 Postgres → pgvector;原型 → Chroma;極致效能 → FAISS;大規模託管 → Pinecone/Qdrant。
- **存正規化向量、用點積(=餘弦)**:省 norm 計算,加速比較。
- **向量綁中繼資料**(原文、類別、來源、時間):支援過濾與回溯來源。
- **先過濾再搜**(按權限/類別/時效):縮小範圍、更準更快。
- **調 ANN 參數權衡速度 vs 召回**(如 HNSW 的 ef):依需求取捨。
- **索引與 embedding 模型一致**:換模型要重建索引(向量空間變了)。
- **文件更新要同步更新向量**:資料變了向量要重 embed。

## Common Mistakes(常見誤解)

- **對百萬向量線性掃描**:O(n),慢到不可用;用 ANN 索引。
- **不正規化又混用度量**:餘弦/點積/歐氏不一致,結果錯。
- **把向量塞進一般 DB 自己算相似度**:慢且難維護;用向量資料庫。
- **不存中繼資料**:檢索到向量卻回溯不到原文/來源。
- **以為 ANN 一定找到真正最近的**:它是近似,可能漏;調參數權衡召回。
- **換 embedding 模型不重建索引**:新舊向量空間不相容,相似度失效。
- **文件更新不同步向量**:檢索到過時內容。
- **不用過濾**:在全庫搜卻只需某類別,浪費且可能撈到不該看的(權限)。

## Interview Notes(面試重點)

- **能說明向量資料庫的角色**:存大量向量 + ANN 索引快速找最相似 + 中繼資料過濾;是語意搜尋/RAG 的檢索引擎。
- **能區分精確 vs 近似最近鄰(ANN)**:O(n) 精確 vs 次線性近似(犧牲一點召回換速度)。
- **知道 HNSW 等 ANN 演算法的概念**(多層圖導航,只查一小部分)。
- **知道正規化 → 點積 = 餘弦,加速比較**。
- **能給選型**:pgvector(Postgres 內)、Chroma(原型)、FAISS(效能)、Pinecone/Qdrant(託管/大規模)。
- **知道中繼資料過濾(先過濾再搜)的價值**(權限/時效)。
- **知道換 embedding 模型要重建索引**。

---

➡️ 下一章:[成本、延遲、快取與限流](08-cost-latency-caching.md)

[⬆️ 回 Part 28 索引](README.md)
