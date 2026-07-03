# 非監督學習:k-means 聚類

> 前面的模型都是**監督式**——有標籤(答案)可學。但很多時候你**沒有標籤**,只想探索資料本身的結構:這批客戶能分成幾群?這些商品有哪些自然類別?這是**非監督學習(unsupervised learning)**,而 **k-means 聚類**是它最經典的入門。它把資料自動分成 k 群,讓「相似的在一起」——無需任何標籤。這章講 k-means 怎麼運作、怎麼選群數、以及它的陷阱。

## Why(為什麼)

現實中,**帶標籤的資料很貴、很少**(要人工標註),但**沒標籤的資料很多**。非監督學習能從無標籤資料挖出價值:

- **客戶分群(segmentation)**:電商有一百萬客戶,沒人幫你標「這是高價值/流失風險/價格敏感」。**聚類**能依消費行為**自動**把客戶分成幾群,行銷團隊再針對各群設計策略。這是 [cohort/商業分析](../24-business-analytics/06-business-metrics.md)之外,發現客群的另一利器。
- **探索資料結構**:一堆資料點,有幾個自然的聚集?聚類幫你**發現隱藏的分組**,常在 [EDA](../23-data-analysis/08-eda.md) 階段揭示洞察(「原來用戶行為有 3 種模式」)。
- **其他應用**:異常偵測(離群點不屬於任何群)、影像壓縮(把顏色聚成 k 種)、文件分組、[推薦系統](../28-llm-genai/06-embeddings-semantic-search.md)的前處理。

**k-means** 是最常用的聚類演算法:給定群數 k,它把資料分成 k 群,讓**每群內部盡量緊密、群間盡量分開**。它簡單、快速、直覺——但有幾個必須理解的陷阱:**要先指定 k(但你常不知道 k 是多少)、對尺度敏感、假設群是圓形的**。這章講原理、選 k 的方法(elbow、silhouette),以及這些陷阱怎麼應對。

## Theory(理論:k-means 演算法)

**k-means 的目標**:把 n 個點分成 k 群,使**組內平方和(inertia,每點到其群中心的距離平方和)** 最小——即每群盡量緊密。

**演算法(迭代)**:

1. **初始化**:隨機選 k 個點當初始「群中心(centroid)」。
2. **指派(assign)**:把每個點分到**最近的**群中心。
3. **更新(update)**:把每群的中心移到該群所有點的**平均位置**。
4. **重複** 2–3,直到中心不再移動(收斂)。

這是「指派 → 更新」的交替最佳化,保證收斂(inertia 單調下降),但**可能收斂到局部最優**——所以要**多次隨機初始化**取最好的(sklearn 的 `n_init`)。

**評估聚類品質**(沒有標籤,怎麼知道分得好?):

- **Inertia(組內平方和)**:越小越緊密。但 k 越大 inertia 必越小(極端:每點一群 inertia=0),不能只看它。
- **Silhouette score(輪廓係數)**:綜合「組內緊密 + 組間分離」,範圍 −1 到 1,**越接近 1 越好**。能用來**選 k**。

## Specification(規範:sklearn 與選 k)

```python
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

km = KMeans(
    n_clusters=3,     # 群數 k(必須事先指定)
    n_init=10,        # 隨機初始化次數(取最好的,避免局部最優)
    random_state=42,
)
km.fit(X)            # X 通常要先標準化!

km.labels_           # 每點的群編號
km.cluster_centers_  # 各群中心座標
km.inertia_          # 組內平方和
silhouette_score(X, km.labels_)   # 聚類品質
```

**選群數 k 的方法**(k-means 最大難題,因為要事先給 k):

- **Elbow method(手肘法)**:畫「k vs inertia」曲線,找**拐點(手肘)**——inertia 急劇下降後趨緩的轉折點,就是好的 k(再增 k 收益不大)。
- **Silhouette method**:試不同 k,選 silhouette score **最高**的。
- **領域知識**:業務上本來就想分幾群(如 3 種客戶等級)。

**前處理鐵律**:**k-means 用距離,一定要先[標準化](../25-machine-learning/03-feature-engineering.md)**(否則大尺度特徵主宰距離)。

## Implementation(底層:為何要標準化、為何選 k 難)

**為何 k-means 必須標準化**:k-means 靠**歐氏距離**把點分到最近的中心。若特徵尺度差很多(如「年齡 20~60」和「收入 30000~120000」),距離幾乎**完全由收入決定**(收入差 10000 的平方遠大於年齡差 10 的平方),年齡形同被忽略——聚類結果只反映收入,無意義([特徵工程](../25-machine-learning/03-feature-engineering.md)講過的距離扭曲問題,在聚類上尤其致命)。**標準化讓每個特徵對距離公平貢獻**,聚類才有意義。這是 k-means 最常被忽略、最致命的錯誤。

**為何選 k 這麼難**:k-means **要你事先給 k,但真實資料你常不知道有幾群**。而且評估陷阱重重——**inertia 隨 k 單調下降**(k 越大每群越小越緊密,極端到「每點一群」inertia=0),所以**不能用「inertia 最小」選 k**(會選到 k=n)。**Elbow method** 的智慧在於:找「inertia **急劇下降後趨緩**」的拐點——在真實群數之前,增加 k 大幅降低 inertia(把混在一起的群分開);超過真實群數後,增加 k 只是把本該同群的硬拆,inertia 降幅驟減。那個「轉折(手肘)」就是自然的群數。下面範例會看到:k 從 1→2→3 時 inertia 從 20121→5527→**363**(劇降),3→4→5 只微降(363→318→273)——**手肘明顯在 k=3**。**Silhouette** 則直接量「分得好不好」,k=3 時最高(0.878)。兩者都正確指向真實群數 3。

**k-means 的假設與侷限**:它假設群是**球形、大小相近、密度均勻**的(因為用「到中心的距離」)。對**非球形(如環狀)、大小懸殊、密度不均**的群,k-means 會分錯——那時要用 DBSCAN、階層聚類等其他方法。理解這個假設,才知道 k-means 何時適用。下面範例示範聚類、elbow、silhouette 選 k。

## Code Example(可執行的 Python 範例)

```python
# clustering.py — k-means 聚類 + elbow + silhouette 選 k(需要 sklearn + numpy)
from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from sklearn.metrics import silhouette_score


def main() -> None:
    # 3 個自然群(真實 k=3)
    X, _ = make_blobs(n_samples=300, centers=3, cluster_std=0.8, random_state=42)

    # Elbow method:inertia 隨 k 下降,找拐點
    print("Elbow method(k vs inertia,找急降後趨緩的拐點):")
    for k in range(1, 6):
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        print(f"  k={k}: inertia={km.inertia_:>7.0f}")
    print("  → k=1→3 劇降(20121→363),3→5 微降 → 手肘在 k=3")

    # Silhouette method:選分數最高的 k
    print("\nSilhouette method(越接近 1 越好):")
    best_k, best_score = 2, -1.0
    for k in range(2, 6):
        km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        score = silhouette_score(X, km.labels_)
        print(f"  k={k}: silhouette={score:.3f}")
        if score > best_score:
            best_score, best_k = score, k
    print(f"  → 最佳 k={best_k}(silhouette={best_score:.3f})")

    # 用最佳 k 聚類
    km = KMeans(n_clusters=best_k, n_init=10, random_state=42).fit(X)
    print(f"\nk={best_k} 聚類結果:各群大小 {np.bincount(km.labels_)}")
    print(f"群中心 shape: {km.cluster_centers_.shape}(k 個中心,每個 2 維)")


if __name__ == "__main__":
    main()
```

**預期輸出**:

```pycon
$ python clustering.py
Elbow method(k vs inertia,找急降後趨緩的拐點):
  k=1: inertia=  20121
  k=2: inertia=   5527
  k=3: inertia=    363
  k=4: inertia=    318
  k=5: inertia=    273
  → k=1→3 劇降(20121→363),3→5 微降 → 手肘在 k=3

Silhouette method(越接近 1 越好):
  k=2: silhouette=0.721
  k=3: silhouette=0.878
  k=4: silhouette=0.697
  k=5: silhouette=0.503
  → 最佳 k=3(silhouette=0.878)

k=3 聚類結果:各群大小 [100 100 100]
群中心 shape: (3, 2)(k 個中心,每個 2 維)
```

逐段解說:

- **Elbow method**:inertia 從 k=1 的 20121、k=2 的 5527、**k=3 的 363**——**劇降**;之後 k=4(318)、k=5(273)只**微降**。**「急降後趨緩」的拐點(手肘)明顯在 k=3**——超過 3 群後,inertia 幾乎不再明顯下降,代表 3 就是自然群數(再分只是硬拆)。**注意不能選 inertia 最小(k=5),要選拐點**。
- **Silhouette method**:直接量聚類品質——k=3 的 0.878 **最高**(組內緊密 + 組間分離最好),k=2、4、5 都較低。**silhouette 明確指向 k=3**,比 elbow 的「看拐點」更客觀。兩種方法都正確找到真實群數 3。
- **聚類結果**:k=3 分出**三群各 100 個**(資料本來就是每群 100 個,分得完美)。`cluster_centers_` 是 3 個 2 維中心座標。這些群編號(`labels_`)就是聚類的產出——**在沒有任何標籤下,自動發現了 3 個群**。
- **實務應用**:這 3 群若是客戶,你可以分析各群特徵(平均消費、年齡...)給它們**命名**(「高價值群」「價格敏感群」),再設計對應策略——**這是非監督學習創造商業價值的方式**。
- **要點**:k-means 迭代「指派→更新中心」把資料分 k 群、要先標準化、用 elbow/silhouette 選 k、假設群是球形。

## Diagram(圖解:k-means 迭代)

```mermaid
flowchart TD
    INIT["1. 隨機放 k 個中心"] --> ASSIGN["2. 每點分到最近中心"]
    ASSIGN --> UPDATE["3. 中心移到各群平均位置"]
    UPDATE --> CHECK{"中心還在動?"}
    CHECK -->|是| ASSIGN
    CHECK -->|否(收斂)| DONE["完成:k 個群"]
    DONE --> K["選 k:elbow(inertia 拐點)<br/>/ silhouette(最高分)"]
    style ASSIGN fill:#e3f2fd
    style UPDATE fill:#fff3e0
    style DONE fill:#e8f5e9
```

## Best Practice(最佳實踐)

- **聚類前一定標準化**:k-means 用距離,大尺度特徵會主宰,必先[標準化](../25-machine-learning/03-feature-engineering.md)。
- **用 elbow + silhouette 選 k**:elbow 找 inertia 拐點、silhouette 選最高分;兩者互相印證。
- **設 `n_init` 多次初始化**:避免收斂到局部最優,取最好的(sklearn 預設會做)。
- **別用 inertia 最小選 k**:inertia 隨 k 單調降,會選到過多群;要看拐點。
- **聚類後分析各群特徵並命名**:賦予群業務意義,才能行動([資料溝通](../24-business-analytics/08-data-storytelling.md))。
- **非球形/密度不均的群改用其他演算法**:DBSCAN、階層聚類、高斯混合。
- **考慮降維後聚類**:高維資料先 [PCA](04-pca.md) 降維,聚類更穩、可視化。
- **聚類是探索性的**:結果沒有絕對「對錯」,要結合領域判斷是否有意義。

## Common Mistakes(常見誤解)

- **不標準化就聚類**:大尺度特徵主宰距離,聚類只反映該特徵,無意義(最致命錯)。
- **用 inertia 最小選 k**:單調下降,會選到過多群(極端每點一群);要看拐點。
- **只跑一次初始化**:可能收斂到差的局部最優;要 `n_init` 多次。
- **對非球形群硬用 k-means**:環狀/密度不均的群會分錯,該換演算法。
- **以為聚類有「正確答案」**:非監督沒有標準答案,要領域判斷群是否有意義。
- **k 亂設不評估**:沒用 elbow/silhouette,群數不合理。
- **聚類後不解讀群**:分完不分析各群特徵,無法轉成行動。
- **高維直接聚類**:維度災難讓距離失去意義,考慮先降維。

## Interview Notes(面試重點)

- **能講 k-means 演算法**:迭代「指派點到最近中心 → 更新中心為群平均」直到收斂,最小化組內平方和。
- **能講為何必須標準化**:用歐氏距離,大尺度特徵主宰,聚類失去意義。
- **能講選 k 的方法**:elbow(inertia 拐點,不能選最小)、silhouette(最高分)、領域知識。
- **能講評估指標**:inertia(組內緊密,但隨 k 單調降)、silhouette(組內+組間,可選 k)。
- **能講 k-means 的假設與侷限**:假設球形/大小相近的群;非球形用 DBSCAN 等。
- **知道多次初始化避免局部最優、聚類是探索性、可先降維。**

---

➡️ 下一章:[降維:PCA](04-pca.md)

[⬆️ 回 Part 26 索引](README.md)
