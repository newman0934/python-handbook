# exercises — 練習題

每題提供函式 stub 與測試，**實作前測試為紅燈**（設計如此），實作後應轉綠。

```text
exercises/
└── partNN/
    ├── <topic>.py         # 待你實作（stub）
    └── test_<topic>.py    # 測試（實作前紅燈）
```

執行：

```bash
pytest exercises        # 實作前部分紅燈，屬正常
```

參考解答見 [`../solutions/`](../solutions/)。

## 目前題目（依 Part 陸續補上）

| Part | 題目 |
|------|------|
| 1 入門 | `fizzbuzz`、`word_frequency` |
| 2 基礎 | `parameters`（args/kwargs）、`closures`、`comprehensions` |
| 3 資料結構 | `dict_ops`、`sequences`（保序去重/分塊）、`sorting_heap`（top-k/合併區間） |
| 4 OOP | `stack`、`shapes`（ABC/多型）、`temperature`（property） |
| 5 typing | `generics`（PEP 695）、`unique_by` |
| 6 錯誤處理 | `safe_ops`（try/except、EAFP）、`context_manager` |
| 7 迭代器/生成器 | `generators`（無限費氏/take）、`pipeline`（惰性分塊） |
| 8 函數式/裝飾器 | `decorators`（memoize）、`compose` |
| 9 併發 | `thread_safe_counter`（Lock）、`parallel_map`、`async_gather` |
| 11 標準庫 | `text_re`（re/slugify）、`collections_ex`（Counter）、`datetime_ex` |

> 🚧 隨各 Part 內容陸續補上。
