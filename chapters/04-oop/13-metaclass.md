# metaclass 元類別

> 如果 class 是「建立實例的工廠」，那 metaclass 就是「建立 class 的工廠」。因為 class 本身也是物件，它必然由某個東西建立——那個東西就是 metaclass，預設是 `type`。

## Why（為什麼）

metaclass 是 Python 最深的特性之一，也是「你可能永遠不用寫、但該理解」的東西。理解它能讓你看懂：class 到底是什麼、ORM（如 Django Model、SQLAlchemy）如何用宣告式語法「魔法般」運作、ABC 如何強制契約、`__init_subclass__` 為何存在。面試到資深職位常問「什麼是 metaclass」。Tim Peters 有句名言：「如果你不確定需不需要 metaclass，那你就不需要」——但**理解**它是另一回事。

## Theory（理論：class 也是物件，由 type 建立）

回到「一切皆物件」（見 [一切皆物件](../10-cpython-internals/01-everything-is-object.md)）：既然 class 也是物件，它必然是「被某個東西建立出來的」。那個東西就是 **metaclass**。

```pycon
>>> class Dog: pass
>>> d = Dog()
>>> type(d)          # 實例的類型是 Dog
<class 'Dog'>
>>> type(Dog)        # Dog 的類型是 type ← type 是 Dog 的 metaclass！
<class 'type'>
>>> type(type)       # type 是它自己的 metaclass
<class 'type'>
```

**關係鏈**：`實例` → 由 `class` 建立；`class` → 由 `metaclass`（預設 `type`）建立。所以：

- `class` 是「產生實例的模板」。
- `metaclass` 是「產生 class 的模板」。

`type` 是 Python 內建的預設 metaclass，所有 class 預設都由它建立。

## Specification（規範：type 的兩種用途、自訂 metaclass）

### `type` 可以動態建立 class

`type(name, bases, namespace)` 這個三參數形式，能在**執行期動態建立 class**（等同 `class` 敘述）：

```python
# 這兩者等價：
class Dog:
    sound = "woof"
    def speak(self):
        return self.sound

Dog = type("Dog", (), {"sound": "woof", "speak": lambda self: self.sound})
```

`class` 敘述其實是「呼叫 metaclass」的語法糖。

### 自訂 metaclass

繼承 `type`，覆寫 `__new__` 或 `__init__` 來「在 class 建立時介入」：

```python
class Meta(type):
    def __new__(mcs, name, bases, namespace):
        # 在這裡可以檢查/修改正在建立的 class
        print(f"建立 class: {name}")
        return super().__new__(mcs, name, bases, namespace)


class MyClass(metaclass=Meta):    # 指定 metaclass
    pass
# 印出「建立 class: MyClass」——在 class 定義時就執行！
```

## Implementation（metaclass 能做什麼 + 更輕量的替代）

### metaclass 在「class 建立時」介入

metaclass 的 `__new__`/`__init__` 在 **class 被定義的當下**執行（不是實例化時）。它拿到 class 的名稱、父類別、命名空間（class 主體的所有內容），能檢查、修改、註冊：

```python
class RegistryMeta(type):
    registry: dict[str, type] = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:                          # 不註冊基底類別自己
            RegistryMeta.registry[name] = cls   # 自動登記所有子類別
        return cls


class Plugin(metaclass=RegistryMeta):
    pass


class AudioPlugin(Plugin): pass
class VideoPlugin(Plugin): pass

print(RegistryMeta.registry)     # {'AudioPlugin': ..., 'VideoPlugin': ...}
```

這就是外掛系統、ORM 自動收集欄位、序列化框架的底層魔法——**每定義一個子類別，metaclass 自動做登記/驗證/改寫**。

### 真實應用：ABC、ORM、dataclass 內部

- **ABC** 用 `ABCMeta`（一個 metaclass）實作「不實作抽象方法就無法實例化」（見 [ABC](10-abc.md)）。
- **Django/SQLAlchemy 的 Model** 用 metaclass 把 `name = CharField()` 這種宣告轉成資料庫欄位映射。
- **Enum**（見 [Enum](14-enum.md)）也靠 metaclass 實作其特殊行為。

### 更輕量的替代：`__init_subclass__` 與類別裝飾器

**大多數「想在 class 建立時做事」的需求，不需要 metaclass**——有更簡單的工具（3.6+）：

**`__init_subclass__`**：父類別定義它，每當有子類別被建立就自動呼叫：

```python
class Plugin:
    registry: dict[str, type] = {}

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        Plugin.registry[cls.__name__] = cls    # 自動登記，不需 metaclass！

class AudioPlugin(Plugin): pass
# Plugin.registry 自動含 AudioPlugin
```

**類別裝飾器**：對已建立的 class 做加工（如 `@dataclass` 就是）：

```python
def add_repr(cls):
    cls.__repr__ = lambda self: f"{cls.__name__}(...)"
    return cls

@add_repr
class Foo: pass
```

**準則**：能用 `__init_subclass__` 或類別裝飾器解決，就別動 metaclass——後者更複雜、且多重繼承時 metaclass 衝突很難處理。

## Code Example（可執行的 Python 範例）

```python
# metaclass_demo.py
from __future__ import annotations


class Meta(type):
    """metaclass：在 class 建立時自動登記。"""

    registry: dict[str, type] = {}

    def __new__(mcs, name: str, bases: tuple, namespace: dict) -> type:
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:  # 跳過基底類別自己
            mcs.registry[name] = cls
        return cls


class Handler(metaclass=Meta):
    pass


class JSONHandler(Handler):
    pass


class XMLHandler(Handler):
    pass


# 更輕量的替代：__init_subclass__
class Plugin:
    plugins: list[str] = []

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        Plugin.plugins.append(cls.__name__)


class PluginA(Plugin):
    pass


def demo() -> None:
    # 1. class 也是物件，type 是它的 metaclass
    print(f"type(Handler) = {type(Handler).__name__}")     # Meta

    # 2. metaclass 自動登記
    print(f"登記表: {sorted(Meta.registry)}")              # ['JSONHandler', 'XMLHandler']

    # 3. type 動態建立 class
    Dynamic = type("Dynamic", (), {"x": 42})
    print(f"動態類別 x = {Dynamic().x}")                    # 42

    # 4. __init_subclass__ 替代方案
    print(f"外掛: {Plugin.plugins}")                        # ['PluginA']


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python metaclass_demo.py
type(Handler) = Meta
登記表: ['JSONHandler', 'XMLHandler']
動態類別 x = 42
外掛: ['PluginA']
```

## Diagram（圖解：實例 → class → metaclass）

```mermaid
flowchart LR
    I["dog 實例"] -->|type| C["Dog 類別"]
    C -->|type / metaclass| M["type (或自訂 Meta)"]
    M -->|type| M2["type 自己"]
    style C fill:#e3f2fd
    style M fill:#fff3e0
```

## Best Practice（最佳實踐）

- **絕大多數情況不要用 metaclass**：優先 `__init_subclass__`（子類別建立時 hook）或**類別裝飾器**（class 加工）——更簡單、更好懂、無衝突風險。
- **只在「框架級」需求才用 metaclass**：需要深度控制 class 建立、且 `__init_subclass__`/裝飾器不夠時（如 ORM、複雜 DSL）。
- **理解 metaclass 是為了讀懂框架**：Django Model、ABC、Enum 的「魔法」都源於此。
- **metaclass 衝突要小心**：多重繼承時，若父類別有不同 metaclass 會 TypeError；讓 metaclass 有共同祖先。
- **自訂 metaclass 記得 `super().__new__(...)`**：保持 type 的正常建立流程。
- **文件化清楚**：metaclass 是隱式魔法，會嚇到讀者；務必註解它做了什麼。

## Common Mistakes（常見誤解）

- **該用 `__init_subclass__`/裝飾器卻硬用 metaclass**：過度工程；後兩者能解決大部分「class 建立時做事」的需求。
- **搞混 metaclass 介入的時機**：它在 **class 定義時**執行（一次），不是每次實例化。
- **metaclass 衝突**：多重繼承下父類別 metaclass 不相容 → `TypeError: metaclass conflict`。
- **混淆 `type(obj)`（查類型）與 `type(name, bases, ns)`（造 class）**：同一個 `type` 的兩種用途。
- **以為 metaclass 很常用**：它是深水區，實務上你可能整個職涯都不用手寫，但該理解。
- **忘了 metaclass 也走繼承**：子類別會繼承父類別的 metaclass。

## Interview Notes（面試重點）

- 說得出核心關係：**實例由 class 建立、class 由 metaclass（預設 `type`）建立**；`type(Dog)` 是 `type`，因為 **class 也是物件**。
- 知道 **`class` 敘述是呼叫 metaclass 的語法糖**，`type(name, bases, namespace)` 能動態造 class。
- 能舉 metaclass 的真實應用：**ABC（ABCMeta）、ORM（Django/SQLAlchemy Model）、Enum**——宣告式框架的底層。
- **關鍵判斷**：知道 **`__init_subclass__` 與類別裝飾器是更輕量的替代**，大多數情況不需要 metaclass。
- 知道 metaclass 在 **class 定義時**介入，以及多重繼承的 metaclass 衝突。

---

➡️ 下一章：[Enum 列舉](14-enum.md)

[⬆️ 回 Part 4 索引](README.md)
