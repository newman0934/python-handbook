# Part 10：CPython 內部與記憶體 CPython Internals & Memory

> 物件模型、引用計數、GC、bytecode、GIL 原理——理解 Python 為何這樣跑。

## 章節

| 章 | 標題 |
|----|------|
| 01 | [一切皆物件](01-everything-is-object.md) |
| 02 | [物件模型：id / type / value](02-object-model.md) |
| 03 | [引用計數 reference counting](03-reference-counting.md) |
| 04 | [循環垃圾回收 GC](04-garbage-collection.md) |
| 05 | [記憶體管理與 arena](05-memory-management.md) |
| 06 | [bytecode 與 dis](06-bytecode-and-dis.md) |
| 07 | [PVM 位元組碼直譯器](07-pvm.md) |
| 08 | [GIL 底層原理](08-gil-internals.md) |
| 09 | [小整數與字串 interning](09-interning.md) |
| 10 | [weakref 弱引用](10-weakref.md) |
| 11 | [適應性直譯器與近期優化 (PEP 659, 3.11+)](11-adaptive-interpreter.md) |
| 12 | [**Part 10 統整：CPython 內部與記憶體全貌**](12-summary.md) |

---

⬅️ 上一 Part：[並發與並行](../09-concurrency/README.md)　｜　➡️ 下一 Part：[標準庫](../11-stdlib/README.md)

[⬆️ 回章節總覽](../README.md)