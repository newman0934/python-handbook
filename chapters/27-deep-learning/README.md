# Part 27：深度學習 Deep Learning

> [集成樹](../26-advanced-ml/02-ensemble-learning.md)在表格資料稱王,但**影像、語音、文字**這些非結構化資料的王者是**深度學習(deep learning)**——用**神經網路(neural network)** 自動學出多層次的特徵表示。這一 Part 從**單一神經元**講起,親手用 numpy **從零刻出一個會學習的神經網路**(前向傳播 + 反向傳播 + 梯度下降),再往上到 CNN、注意力機制、訓練技巧。重點是**理解神經網路到底怎麼運作**,而非只會呼叫框架——這是理解 [LLM](../28-llm-genai/README.md) 的根基。

> 🧭 屬「**資料 / AI 學習線**」,對應 **Machine Learning Engineer**(深度學習方向)。前置:[Part 25 ML 基礎](../25-machine-learning/README.md)(尤其[梯度下降的直覺](../25-machine-learning/04-linear-regression.md)、[邏輯回歸](../25-machine-learning/05-classification.md))。範例用**純 numpy 手刻**(不需 GPU/框架),PyTorch 以程式碼示意(概念呼應);CI 已含 `data` 依賴。

## 章節

| 章 | 標題 |
|----|------|
| 01 | [神經網路基礎](01-neural-network-basics.md) |
| 02 | [反向傳播與梯度下降](02-backpropagation.md) |
| 03 | [從零手刻神經網路](03-nn-from-scratch.md) |
| 04 | [深度學習框架 PyTorch](04-frameworks.md) |
| 05 | [CNN 卷積神經網路](05-cnn.md) |
| 06 | [序列模型與注意力](06-sequence-attention.md) |
| 07 | [訓練技巧](07-training-techniques.md) |
| 08 | [🏗️ Capstone:從零訓練神經網路](08-capstone-nn.md) |

---

⬅️ 上一 Part：[進階機器學習](../26-advanced-ml/README.md)

➡️ 銜接：[Part 28 LLM 與生成式 AI](../28-llm-genai/README.md)(注意力/transformer 的延伸)

[⬆️ 回章節總覽](../README.md)
