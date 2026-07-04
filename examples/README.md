# examples — 可執行範例

各章對應的可執行 Python 範例，附 `test_*.py`，以 `pytest` 驗證行為。

```text
examples/
└── partNN/            # 對應章節 Part 編號
    ├── <topic>.py
    └── test_<topic>.py
```

執行：

```bash
pytest examples
```

> ✅ 全 31 Part 皆有可執行範例與 `test_*.py`,`pytest examples` 應全綠。
