# Part 25 面試題:機器學習基礎

> 對應 [Part 25 機器學習基礎](../chapters/25-machine-learning/README.md)。**ML Engineer 核心**——train/test split、資料洩漏、過擬合、混淆矩陣、Pipeline。

---

## Q1. 傳統程式和機器學習差在哪?什麼時候該用 ML?

**考點**:ML 概論([01-ml-intro](../chapters/25-machine-learning/01-ml-intro.md))

**答**:

- **傳統程式**:規則 + 資料 → 答案(**你寫規則**)。
- **機器學習**:資料 + 答案 → **規則(模型)**(程式學規則)。

**該用 ML**:規則**寫不出來**(垃圾信、影像辨識)+ 有足夠資料 + 容忍機率性錯誤。**簡單規則能解就別用 ML**(`if age>=18` 別訓練模型)。

**追問**:三大類型——監督(回歸/分類)、非監督(聚類/降維)、強化學習;回歸(預測**連續數值**)vs 分類(預測**類別**);目的是**泛化**(對新資料表現好),不是記住訓練資料。

---

## Q2.(必考)為什麼要 train/test split?什麼是資料洩漏?

**考點**:工作流([02-ml-workflow](../chapters/25-machine-learning/02-ml-workflow.md))

**答**:**必須用模型「沒見過」的資料評估泛化**——訓練資料上的分數會騙人(背答案也能高分)。三種資料集:**train(學)、validation(調參選模型)、test(最終一次評估)**。

**資料洩漏(致命)**:test 資訊洩漏進訓練——最經典是**在 split 之前做前處理**(標準化算了整份資料含 test 的統計量),導致**分數虛高、上線暴跌、還不報錯**。

防法:**前處理參數只 `fit` 在 train、`transform` 套到 test**(絕不 fit test):

```python
scaler.fit_transform(X_train)   # 只從 train 學 mean/std
scaler.transform(X_test)         # 用 train 的統計,不 fit!
```

**追問**:用 [Pipeline](#q8必考-pipeline-為什麼能防資料洩漏) 從結構上防洩漏;test 只用一次(調參用 CV/validation);分類用 stratify 保類別比例。

---

## Q3. 特徵工程有多重要?什麼時候要標準化?one-hot 和 label encoding 怎麼選?

**考點**:特徵工程([03-feature-engineering](../chapters/25-machine-learning/03-feature-engineering.md))

**答**:「**資料/特徵決定上限,模型只是逼近上限**」——特徵工程常比換模型更能提升表現。

- **標準化**:**距離/梯度型模型需要**(線性、KNN、SVM、神經網路——否則大尺度特徵主宰);**樹模型不需要**(按閾值分割,尺度無關)。
- **one-hot vs label encoding**:**無序類別用 one-hot**(獨立 0/1 欄,正交無大小);**label encoding 會強加虛假順序**(把城市編成 0/1/2,模型誤以為有大小),只適合**有序類別**或**樹模型**。

**追問**:特徵衍生(用領域知識造比值/交互,把規律直接餵給模型)——簡單模型立即能用。

---

## Q4. 線性回歸的模型和損失?怎麼解讀係數?回歸指標有哪些?

**考點**:線性回歸([04-linear-regression](../chapters/25-machine-learning/04-linear-regression.md))

**答**:模型:**ŷ = 加權和 + 截距**(`w₁x₁ + ... + b`),學習目標是**最小化 MSE**。

**為何用平方誤差**:正負不抵消、放大大誤差(模型特別避免大錯)、可微分(便於最佳化)。

**係數可解讀**:`wᵢ` = 特徵 xᵢ 每增一單位對結果的影響(其他固定)——這是線性回歸的**可解釋性**來源。

**回歸指標**:MSE、**RMSE**(√MSE,回到**原單位**,對業務溝通用)、MAE(對離群穩健)、**R²**(解釋變異比例,0~1,**跨資料集可比**)。

**追問**:R² = 1 完美、= 0 等於猜平均、可為負(比猜平均還差)。

---

## Q5. 邏輯回歸怎麼做分類?為什麼不用線性回歸做分類?

**考點**:分類([05-classification](../chapters/25-machine-learning/05-classification.md))

**答**:**邏輯回歸 = 線性組合 + sigmoid**——`z = w·x + b`(無界)→ **sigmoid 壓到 (0,1)** 變機率 → 依閾值(預設 0.5)分類。

**為何不用線性回歸**:線性回歸輸出**無界**(可能 1.7 或 −0.3),**無機率意義**;分類要 (0,1) 的機率。

**sigmoid** 性質:S 形、`σ(0)=0.5`、把實數壓到 (0,1)、可微。損失用 **log loss(交叉熵)**——**重罰自信的錯誤**(說 99% 卻錯,懲罰巨大),配 sigmoid 是凸的(好最佳化)。

**追問**:輸出**機率**(`predict_proba`)而非只類別,讓你能**調閾值**平衡 precision/recall(不必重訓);詐騙/疾病降閾值提高 recall。

---

## Q6.(必考)準確率為什麼在不平衡資料上誤導?precision 和 recall 差在哪?

**考點**:模型評估([06-model-evaluation](../chapters/25-machine-learning/06-model-evaluation.md))

**答**:1000 筆交易只 50 筆詐騙,一個「**全部猜正常**」的模型準確率 95%,但 **recall = 0**(一個詐騙都沒抓到)——準確率被**多數類主宰**,毫無用處。

**混淆矩陣**(以詐騙=正類):

```text
              預測正常   預測詐騙
真實正常      TN        FP(誤報)
真實詐騙      FN(漏報)  TP
```

- **Precision = TP/(TP+FP)**:判為詐騙的**有多少真的是**(衡量誤報,**別誤傷**)。
- **Recall = TP/(TP+FN)**:真詐騙**有多少被抓到**(衡量漏報,**別放過**)。

**取捨**:此消彼長——詐騙/疾病看 **recall**(別放過)、垃圾過濾看 **precision**(別誤傷);調閾值調平衡。**F1** 是調和平均(逼兩者都要好)。

**追問**:**AUC**(與閾值無關的整體區分力,用機率算,適合比較模型);不平衡資料**絕不能只看準確率**。

---

## Q7.(必考)什麼是過擬合?怎麼診斷?正則化和交叉驗證怎麼對付它?

**考點**:過擬合([07-overfitting-regularization](../chapters/25-machine-learning/07-overfitting-regularization.md))

**答**:

- **過擬合**:模型**背住訓練資料(含雜訊)**——**訓練好、測試差**(高變異)。
- **欠擬合**:模型太簡單——**訓練、測試都差**(高偏差)。

**診斷**:比較 **train 分數 vs test 分數**——差距大 = 過擬合、都低 = 欠擬合。**bias-variance tradeoff**:目標是總誤差最小的平衡點。

**正則化**:**懲罰大權重、限制複雜度**——L2(Ridge,平滑)、L1(Lasso,稀疏/特徵選擇)。`α` 控強度(太大欠擬合、太小過擬合)。

**交叉驗證(k-fold)**:把 train 切 k 份,輪流當驗證,**平均更可靠**、給穩定度——用來**調參**,**test 留到最後**。

**追問**:對付過擬合的手段——更多資料、簡化模型、正則化、CV 調參、[dropout/early stopping](part27-deep-learning.md)。

---

## Q8.(必考)Pipeline 為什麼能防資料洩漏?

**考點**:端到端 ML([08-capstone-ml](../chapters/25-machine-learning/08-capstone-ml.md))

**答**:端到端流程:**split → Pipeline → CV 選參 → 全 train 重訓 → test 評估**(順序不能錯)。

**Pipeline 防洩漏**:它把「前處理 + 模型」綁成一個物件。做 CV 時,**每一折內部自動只從該折的訓練部分學前處理參數**(標準化的 mean/std),再套到驗證折——**手動做極易洩漏**(不小心用了整個 train 的統計),Pipeline 從結構上杜絕:

```python
pipe = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression())])
cross_val_score(pipe, X_train, y_train, cv=5)   # 每折自動防洩漏
```

**追問**:**CV 選參與 test 評估分離**(test 全程零接觸直到最後,保證泛化估計誠實);**選對指標**(不平衡看 F1/AUC/每類 P/R);追求**可信估計**而非高分(高分常來自洩漏)。

---

⬅️ [Part 24](part24-business-analytics.md) ｜ [索引](README.md) ｜ ➡️ [Part 26 進階機器學習](part26-advanced-ml.md)
