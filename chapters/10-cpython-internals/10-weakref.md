# weakref 弱引用

> 弱引用「指向物件但不增加引用計數」——它不會阻止物件被回收。用它做快取、觀察者、避免循環引用，能持有物件卻不延長其壽命。

## 💡 白話導讀（建議先讀）

普通的引用像**拉著一個人的手**——只要還有一隻手拉著（[計數牌](03-reference-counting.md) > 0），這個人就走不了（不會被回收）。

但有些場景，你想「**看著他，但不留住他**」：

**弱引用（weakref）＝遠遠看著,不拉手**：

```python
import weakref

ref = weakref.ref(obj)     # 看著 obj —— 但計數牌「不 +1」
ref()                      # 他還在 → 拿到本人
del obj                    # 最後一隻拉著的手放開 → 他正常離開(被回收)
ref()                      # None —— 你看到的是空位
```

重點兩條：**弱引用不阻止回收**;對方走了之後,弱引用**自動失效**（回傳 None,不會變成懸空指標）。

什麼場景需要「看而不留」？

1. **快取**:想快取物件加速,但**不希望「因為被快取著」而永遠不死**——物件沒人用了就該走,快取自動出空位（現成工具:`WeakValueDictionary`）。
2. **觀察者/回呼註冊表**:名單上登記了一堆物件——不該因為「在名單上」就永生。
3. **打破循環引用**:[第 4 章](04-garbage-collection.md)的「互相扶持」——把其中一隻手改成弱引用（孩子弱引用父母）,循環就不成立,計數制度直接解決,連 GC 都不用出動。

一句話:**強引用是「擁有」,弱引用是「認識」**——不想因為認識而綁住對方的壽命,就用弱的。

## Why（為什麼）

[引用計數](03-reference-counting.md) 告訴我們：只要有引用指向物件，它就不會被回收。但有時你想「參照一個物件、卻**不想**因此讓它活著」——例如快取（快取不該阻止物件被回收）、觀察者（觀察者不該讓被觀察者永生）、打破循環引用。**弱引用（weak reference）** 正是為此：它指向物件但**不增加引用計數**，物件該回收時照樣回收，弱引用則自動失效。這是解決「快取記憶體洩漏」「循環引用」等實際問題的工具。

## Theory（理論：不計入引用計數的引用）

**弱引用**：能存取一個物件、但**不增加其引用計數**的特殊引用（見[引用計數](03-reference-counting.md)）——「看著，不拉手」。後果：

- 若物件**只剩弱引用**指向它（沒有任何強引用），它會被**正常回收**。
- 回收後，弱引用**自動失效**（呼叫它回傳 `None`，或觸發回呼）——不會變懸空指標。

對比：

- **強引用（一般引用）**：`x = obj` → 計數 +1 → 阻止回收——「擁有」。
- **弱引用**：`ref = weakref.ref(obj)` → 計數**不變** → 不阻止回收——「認識」。

弱引用讓你「觀察但不擁有」——快取、觀察者名單、打破循環引用等「不想因參照而延長物件壽命」的場景。

## Specification（規範：weakref 模組）

```python
import weakref

# 基本弱引用
ref = weakref.ref(obj)      # 建立弱引用
obj_again = ref()           # 呼叫取得物件（若已回收回 None）

# 弱引用字典/集合（key 或 value 是弱引用）
weakref.WeakValueDictionary()   # value 是弱引用（value 被回收則自動移除該項）
weakref.WeakKeyDictionary()     # key 是弱引用
weakref.WeakSet()               # 元素是弱引用

# finalize：物件回收時執行清理
weakref.finalize(obj, cleanup_func, *args)

# proxy：像物件本身一樣用（但底層是弱引用）
proxy = weakref.proxy(obj)
```

⚠️ 注意：**不是所有物件都能被弱引用**——`int`、`str`、`tuple`、以及沒有 `__weakref__` 的內建型別不行；自訂類別預設可以。

## Implementation（基本弱引用、WeakValueDictionary、打破循環）

### 基本弱引用：物件回收後自動失效

```python
import weakref

class Data:
    def __init__(self, value): self.value = value

obj = Data(42)
ref = weakref.ref(obj)      # 弱引用，不增加引用計數

print(ref())                # <Data object>（物件還活著）
print(ref().value)          # 42

del obj                     # 刪除唯一的強引用 → 物件被回收
print(ref())                # None（弱引用失效）
```

`del obj` 後，因為 `ref` 是弱引用（沒撐著物件），物件被回收，`ref()` 回 `None`。這就是「持有參照卻不延長壽命」。

### `WeakValueDictionary`：不洩漏的快取

普通 dict 當快取有個問題——**它持有強引用，被快取的物件永遠不會被回收**（即使外界不再用），造成記憶體滯留。`WeakValueDictionary` 的 value 是弱引用，物件一旦沒有外部強引用就自動從快取移除：

```python
import weakref

# ❌ 普通 dict 快取：物件永遠不被回收（記憶體洩漏風險）
cache = {}
cache[key] = expensive_obj    # 強引用，撐著物件

# ✅ WeakValueDictionary：物件沒外部引用就自動移除
cache = weakref.WeakValueDictionary()
cache[key] = expensive_obj    # 弱引用
# 當 expensive_obj 沒有其他強引用時，自動從 cache 消失
```

這是弱引用最實用的場景——**快取不阻止被快取物件的回收**，避免「快取越積越多、記憶體不釋放」。

### 打破循環引用

雖然循環 GC 能回收循環（見 [GC](04-garbage-collection.md)），但用弱引用**主動打破循環**更即時、更乾淨——尤其父子互指的結構：

```python
import weakref

class Parent:
    def __init__(self):
        self.children = []

class Child:
    def __init__(self, parent):
        self.parent = weakref.ref(parent)   # 弱引用父親，打破循環！

parent = Parent()
child = Child(parent)
parent.children.append(child)   # parent → child（強）
# child → parent 是弱引用，不形成循環
# 所以 del parent 後，引用計數就能回收（不必等循環 GC）
```

「父持有子（強）、子參照父（弱）」是常見模式——避免父子互相強引用形成循環，讓引用計數能即時回收。

### `finalize`：物件回收時的清理

`weakref.finalize` 註冊「物件被回收時要執行的清理」——比 `__del__` 更可靠、可預測：

```python
import weakref

def cleanup(name):
    print(f"清理 {name}")

obj = SomeResource()
weakref.finalize(obj, cleanup, "資源A")   # obj 被回收時呼叫 cleanup("資源A")
```

比 `__del__` 好的地方：不會因循環引用而不執行、行為更明確。但重要的資源清理仍優先用 `with`（見 [context manager](../06-error-handling/06-context-manager.md)）。

## Code Example（可執行的 Python 範例）

```python
# weakref_demo.py
from __future__ import annotations

import weakref


class Data:
    def __init__(self, value: int) -> None:
        self.value = value


def basic_weakref() -> tuple[int, None]:
    """弱引用不阻止回收。"""
    obj = Data(42)
    ref = weakref.ref(obj)
    alive = ref().value if ref() else -1  # 物件還活著

    del obj  # 刪除唯一強引用
    dead = ref()  # 弱引用失效 → None
    return alive, dead


def weak_cache_demo() -> tuple[bool, bool]:
    """WeakValueDictionary：物件沒外部引用就自動移除。"""
    cache: weakref.WeakValueDictionary[str, Data] = weakref.WeakValueDictionary()

    obj = Data(100)
    cache["key"] = obj
    in_cache_before = "key" in cache  # True（obj 還有強引用）

    del obj  # 移除外部強引用
    in_cache_after = "key" in cache  # False（自動移除）
    return in_cache_before, in_cache_after


def demo() -> None:
    # 1. 基本弱引用
    alive, dead = basic_weakref()
    print(f"物件活著時: {alive}")
    print(f"物件回收後弱引用: {dead}")

    # 2. WeakValueDictionary 快取
    before, after = weak_cache_demo()
    print(f"\n快取中（有強引用時）: {before}")
    print(f"快取中（無強引用後）: {after}")


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python weakref_demo.py
物件活著時: 42
物件回收後弱引用: None

快取中（有強引用時）: True
快取中（無強引用後）: False
```

## Diagram（圖解：強引用 vs 弱引用）

```mermaid
flowchart TD
    subgraph strong [強引用]
        S1[x = obj] -->|引用計數 +1| SO[物件存活]
    end
    subgraph weak [弱引用]
        W1[ref = weakref.ref obj] -.不增加計數.-> WO[物件]
        WO -->|唯一強引用消失| WR[物件回收, ref() → None]
    end
    style SO fill:#e3f2fd
    style WR fill:#fff3e0
```

## Best Practice（最佳實踐）

- **快取用 `WeakValueDictionary`/`WeakKeyDictionary`**：避免快取阻止物件回收（記憶體洩漏）；被快取物件沒外部引用就自動移除。
- **打破循環引用用弱引用**：父子互指時，讓「子→父」是弱引用——避免循環、讓引用計數即時回收。
- **觀察者/回呼用弱引用**：觀察者不該讓被觀察者永生；用 weakref 避免。
- **清理用 `weakref.finalize`** 比 `__del__` 可靠；但重要資源仍用 `with`。
- **記得不是所有物件可弱引用**：`int`/`str`/`tuple` 等內建不行；需要弱引用的自訂類別預設可以。
- **弱引用取值後檢查 `None`**：物件可能已被回收，`ref()` 回 `None` 要處理。

## Common Mistakes（常見誤解）

- **用普通 dict 當快取造成記憶體滯留**：強引用撐著物件永不回收；用 `WeakValueDictionary`。
- **對 `int`/`str`/`tuple` 建弱引用**：`TypeError: cannot create weak reference`；這些內建型別不支援。
- **忘了弱引用可能失效**：`ref()` 可能回 `None`（物件已回收），取值前要檢查。
- **以為弱引用能阻止回收**：相反——它**不**阻止回收（這正是重點）。
- **父子都用強引用**：形成循環，靠循環 GC 才能回收（延遲）；讓一方向弱引用更好。
- **依賴 `__del__` 清理而不用 `finalize`/`with`**：`__del__` 時機不保證。

## Interview Notes（面試重點）

- **能說明弱引用**：指向物件但**不增加引用計數**，故**不阻止回收**；物件回收後弱引用失效（`ref()` 回 `None`）。
- **知道主要用途**：**快取（WeakValueDictionary，避免快取阻止回收 → 防記憶體洩漏）、打破循環引用（父子互指時子用弱引用）、觀察者**。
- 知道 **不是所有物件可弱引用**（`int`/`str`/`tuple` 等不行）。
- 知道 **`weakref.finalize`** 比 `__del__` 可靠的清理，但重要清理仍用 `with`。
- 能連結 [引用計數](03-reference-counting.md)/[GC](04-garbage-collection.md)：弱引用是「持有參照卻不延長壽命」，用於解決引用計數/循環引用的實際問題。

---

➡️ 下一章：[適應性直譯器與近期優化 (PEP 659, 3.11+)](11-adaptive-interpreter.md)

[⬆️ 回 Part 10 索引](README.md)
