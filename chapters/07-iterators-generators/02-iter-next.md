# __iter__ 與 __next__

> 自己寫可迭代物件時，關鍵是把「容器」和「迭代狀態」分開——`__iter__` 每次回傳一個全新的、帶獨立進度的 iterator。搞錯這點，你的物件就無法被同時或重複遍歷。

## Why（為什麼）

上一章講了協定的概念，這章實作它。你可能想讓自訂類別支援 `for`——例如一個資料結構、一個資料流。正確做法有個關鍵設計決策：**iterator 的狀態該放哪？** 放錯地方（把進度放在容器自己身上）會導致「不能重複遍歷」「巢狀遍歷互相干擾」的 bug。這章講清楚正確的分離設計，以及「用生成器一行搞定」的捷徑。

## Theory（理論：容器與迭代狀態分離）

實作迭代協定有兩種角色，關鍵是**把它們分開**：

- **容器（iterable）**：持有資料，實作 `__iter__` —— 每次呼叫都**回傳一個新的 iterator**。
- **iterator**：持有「遍歷到哪」的狀態，實作 `__next__`（回下一個 / raise StopIteration）和 `__iter__`（回自己）。

**為什麼要分開？** 因為「遍歷進度」是一次遍歷的狀態，不該屬於容器本身。若把進度放在容器上，那容器就只能被遍歷一次、也無法巢狀遍歷（兩個 `for` 同時跑會共用進度、互相干擾）。

## Specification（規範：兩種實作方式）

```python
# 方式一：容器 + 獨立 iterator 類別（正確的分離）
class Container:
    def __init__(self, items): self.items = items
    def __iter__(self): return ContainerIterator(self.items)   # 每次回新的

class ContainerIterator:
    def __init__(self, items):
        self.items = items
        self.index = 0                      # 進度放這裡（每個 iterator 獨立）
    def __iter__(self): return self
    def __next__(self):
        if self.index >= len(self.items):
            raise StopIteration
        value = self.items[self.index]
        self.index += 1
        return value

# 方式二：__iter__ 用生成器（最簡潔，通常首選）
class Container:
    def __init__(self, items): self.items = items
    def __iter__(self):
        yield from self.items               # 生成器天生是新的 iterator
```

## Implementation（分離設計、反例、生成器捷徑）

### 正確：容器與 iterator 分離 → 可重複、可巢狀

```python
class NumberRange:
    def __init__(self, start: int, stop: int) -> None:
        self.start = start
        self.stop = stop
    def __iter__(self) -> "RangeIterator":
        return RangeIterator(self.start, self.stop)   # 每次新的

class RangeIterator:
    def __init__(self, current: int, stop: int) -> None:
        self.current = current      # 獨立進度
        self.stop = stop
    def __iter__(self): return self
    def __next__(self) -> int:
        if self.current >= self.stop:
            raise StopIteration
        value = self.current
        self.current += 1
        return value
```

因為每次 `iter()` 給一個帶獨立進度的新 iterator，`NumberRange` 可以重複遍歷、巢狀遍歷都正常——就像內建的 `range`。

### 反例：把進度放容器身上（只能遍歷一次）

```python
# ❌ 錯誤：容器自己當 iterator，進度在自己身上
class BadRange:
    def __init__(self, stop: int) -> None:
        self.current = 0            # 進度在容器上！
        self.stop = stop
    def __iter__(self): return self
    def __next__(self) -> int:
        if self.current >= self.stop:
            raise StopIteration
        self.current += 1
        return self.current - 1

r = BadRange(3)
print(list(r))     # [0, 1, 2]
print(list(r))     # []  ← 第二次是空的！進度沒重置
```

`BadRange` 用完就無法再遍歷（進度停在終點），且兩個巢狀 `for r` 會共用 `current` 互相破壞。這是「容器兼當 iterator」的通病——**除非你確實想要「一次性」語意，否則要分離**。

### 最簡潔：`__iter__` 用生成器

實務上**幾乎不必手寫 iterator 類別**——直接讓 `__iter__` 成為生成器（見 [生成器](03-generator.md)），每次呼叫自動產生一個新的、獨立的 iterator：

```python
class NumberRange:
    def __init__(self, start: int, stop: int) -> None:
        self.start = start
        self.stop = stop
    def __iter__(self):
        current = self.start
        while current < self.stop:
            yield current            # 生成器：每次 __iter__ 回新的 iterator
            current += 1
```

這版和前面「分離的兩類別」行為完全一樣（可重複、可巢狀），但只要幾行。**這是現代 Python 寫可迭代物件的首選**——把迭代邏輯寫成生成器，享有分離的好處而無需樣板。

## Code Example（可執行的 Python 範例）

```python
# iter_next_demo.py
from __future__ import annotations

from collections.abc import Iterator


class Fibonacci:
    """用生成器 __iter__ 實作可重複遍歷的費氏數列（前 n 項）。"""

    def __init__(self, n: int) -> None:
        self.n = n

    def __iter__(self) -> Iterator[int]:
        a, b = 0, 1
        for _ in range(self.n):
            yield a
            a, b = b, a + b


class ManualRange:
    """手寫分離式（容器 + iterator），對照生成器版。"""

    def __init__(self, stop: int) -> None:
        self.stop = stop

    def __iter__(self) -> ManualRangeIterator:
        return ManualRangeIterator(self.stop)


class ManualRangeIterator:
    def __init__(self, stop: int) -> None:
        self.current = 0
        self.stop = stop

    def __iter__(self) -> ManualRangeIterator:
        return self

    def __next__(self) -> int:
        if self.current >= self.stop:
            raise StopIteration
        value = self.current
        self.current += 1
        return value


def demo() -> None:
    fib = Fibonacci(8)
    print(f"費氏第一次: {list(fib)}")     # [0,1,1,2,3,5,8,13]
    print(f"費氏第二次: {list(fib)}")     # 同上（可重複）

    # 巢狀遍歷（每個 for 各自獨立進度）
    r = ManualRange(3)
    pairs = [(a, b) for a in r for b in r]
    print(f"巢狀對: {pairs}")             # 9 對，證明可巢狀


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python iter_next_demo.py
費氏第一次: [0, 1, 1, 2, 3, 5, 8, 13]
費氏第二次: [0, 1, 1, 2, 3, 5, 8, 13]
巢狀對: [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
```

## Diagram（圖解：分離設計）

```mermaid
flowchart TD
    C["容器 (iterable)<br/>__iter__ 每次回新的"] -->|iter()| I1["iterator #1<br/>獨立進度"]
    C -->|iter()| I2["iterator #2<br/>獨立進度"]
    Note["兩次遍歷/巢狀遍歷 → 各自獨立 → 互不干擾"]
    style C fill:#e3f2fd
    style I1 fill:#e8f5e9
    style I2 fill:#e8f5e9
```

## Best Practice（最佳實踐）

- **首選：讓 `__iter__` 成為生成器**（`yield`），幾行就得到「可重複、可巢狀」的正確行為，無需樣板。
- **需要手寫 iterator 時，分離容器與進度**：`__iter__` 回新 iterator、進度放 iterator 身上。
- **只有確實要「一次性」語意時，才讓容器兼當 iterator**（如串流、一次性資料源）——並明確文件化。
- **iterator 的 `__iter__` 回傳 `self`**，`__next__` 耗盡時 `raise StopIteration`。
- **型別註記用 `Iterator[T]`**（`__iter__` 回傳）與 `Iterable[T]`。
- **用 `yield from self.items` 委派給既有可迭代物件**（見 [yield from](05-yield-from.md)），最省事。

## Common Mistakes（常見誤解）

- **把進度放在容器上（容器兼 iterator）**：導致「只能遍歷一次」「巢狀遍歷互相破壞」——最常見的 bug。
- **`__iter__` 回傳 self 但沒重置進度**：第二次遍歷是空的。
- **iterator 忘了 `__iter__`（回自己）**：無法直接用於 `for`。
- **`__next__` 忘了 raise StopIteration**：迴圈永不結束（無窮迴圈）。
- **手寫一堆 iterator 樣板**：多數情況生成器 `__iter__` 更簡潔，別造輪子。
- **誤以為分離設計很麻煩**：用生成器 `__iter__` 一點都不麻煩。

## Interview Notes（面試重點）

- **能說出正確設計：容器（`__iter__` 每次回新 iterator）與 iterator（持有進度、`__next__` + `__iter__` 回自己）分離**，以及為何分離（可重複、可巢狀遍歷）。
- 能指出「**容器兼當 iterator**」的問題（只能遍歷一次、巢狀互相干擾）與適用時機（一次性串流）。
- 知道 **最簡潔的做法是讓 `__iter__` 成為生成器**，自動獲得分離的好處。
- 知道 `__next__` 耗盡 `raise StopIteration`、iterator 的 `__iter__` 回 self。
- 能寫出自訂可迭代物件（生成器版與手寫版皆可）。

---

➡️ 下一章：[生成器 generator 與 yield](03-generator.md)

[⬆️ 回 Part 7 索引](README.md)
