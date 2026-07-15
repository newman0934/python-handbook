# 繼承

> 繼承讓子類別重用並擴充父類別；而 `super()` 是正確呼叫父類別方法的關鍵——它不只是「呼叫父類別」，在多重繼承下還牽涉整條 MRO。

## 💡 白話導讀（建議先讀）

先不談程式，想一件生活中的事。

你開了一家飲料店，生意不錯，決定開分店。
分店要不要重寫一份完整的員工手冊？不用——直接沿用總店的就好。

這就是「繼承」：**分店（子類別）自動擁有總店（父類別）的所有做法**。

但分店可以有自己的變化：

- 總店手冊寫「珍珠煮 30 分鐘」，分店照做——這是**直接繼承**，什麼都不用寫。
- 分店覺得在地口味不同，自己規定「珍珠煮 40 分鐘」——這是**覆寫（override）**：同一件事，換成自己的做法。
- 分店說「照總店的方式煮，但最後多加一匙黑糖」——這是 `super()`：**先照父類別的做法，再加上自己的**。

還有一個常見的坑，先打預防針。
分店開幕時要做的準備工作（程式裡叫 `__init__`），如果你自己寫了一份，總店那份**不會自動執行**。
所以子類別寫 `__init__` 時，要記得先呼叫 `super().__init__()`——意思是「先做總店的開店準備，再做自己的」。
忘了這一步，店就少了總店該準備的東西（程式裡的症狀是：某個屬性不存在、一用就報錯）。

最後一個判斷題：什麼時候**不該**用繼承？
問自己一句話：「A **是一種** B 嗎？」

- 狗**是一種**動物 → 用繼承（術語叫 is-a）。
- 車**是一種**引擎？不對，車是「**有一個**引擎」→ 不要用繼承，把引擎當成車的一個屬性就好（這叫「組合」，has-a）。

帶著這四個畫面——**沿用手冊、自己改做法、照做再加料、開幕準備要先做總店的**——往下讀正式內容就不會迷路了。

## 🔗 前端對照

繼承在 Python 和 JavaScript 概念一致,語法對照:

| | Python | JavaScript |
|---|--------|-----------|
| 繼承 | `class Dog(Animal):` | `class Dog extends Animal {}` |
| 呼叫父類 | `super().__init__()` | `super()` / `super.method()` |
| 多重繼承 | **支援**（搭配 MRO 決定順序） | **不支援**（只能單繼承 + mixin 技巧） |

一句話:單繼承幾乎一樣。最大差異——**Python 支援多重繼承**（一個 class 可繼承多個父類,靠 MRO 排順序,見下一章）;
JS 只能單繼承,要組合多來源得用 mixin 手法。

## Why（為什麼）

當多個類別有共同的行為與屬性，繼承讓你把共通部分抽到父類別、子類別只寫差異，避免重複。但繼承用不好會變成脆弱的深層階層。這章講清楚繼承語法、方法覆寫、`super()` 的正確用法（尤其 `__init__` 的鏈式呼叫），以及「什麼時候該用繼承、什麼時候該用組合」——後者是資深工程師的判斷。

## Theory（理論：is-a 關係與方法解析）

繼承在說的是一種「分類」關係：**A 是一種 B**（術語叫 is-a）。

狗是一種動物、轎車是一種車輛。
在程式裡寫成 `class Dog(Animal):`，讀作「Dog 繼承 Animal」。
被繼承的叫**父類別**（superclass），去繼承別人的叫**子類別**（subclass）。

繼承之後，子類別拿到什麼？
答案是：**父類別的所有屬性和方法，全部自動擁有**——就像分店直接沿用總店手冊，一個字都不用重抄。

在這個基礎上，子類別可以做三件事（對應導讀的三個畫面）：

1. **新增**：加上父類別沒有的屬性或方法（分店多賣一款限定飲品）。
2. **覆寫（override）**：同名方法重新定義，換成自己的做法（珍珠改煮 40 分鐘）。
3. **擴充**：用 `super()` 先執行父類別的版本，再加上自己的（照總店煮法，最後加黑糖）。

最後一個問題：當你呼叫 `dog.speak()`，Python 怎麼決定用「誰的」`speak`？

規則很單純：**從子類別開始往父類別找，找到第一個就用**。
Dog 自己有 `speak` → 用 Dog 的；Dog 沒有 → 往上用 Animal 的。
這個「尋找的順序」有個正式名字：**MRO（Method Resolution Order，方法解析順序）**。
單一繼承下它就是「由子到父」這麼直觀；到了[多重繼承](04-mro.md)它才會變複雜——下一章專門講它。

## Specification（規範：繼承語法）

```python
class Animal:                     # 父類別
    def __init__(self, name: str) -> None:
        self.name = name

    def speak(self) -> str:
        return "..."

    def describe(self) -> str:
        return f"{self.name} says {self.speak()}"


class Dog(Animal):                # 繼承 Animal
    def speak(self) -> str:       # 覆寫
        return "Woof"


class Puppy(Dog):                 # 多層繼承
    def __init__(self, name: str, age: int) -> None:
        super().__init__(name)    # 呼叫父類別 __init__
        self.age = age
```

- `class Sub(Base):` 表示繼承。
- `isinstance(obj, Cls)` 檢查是否為某類別（含子類別）的實例；`issubclass(A, B)` 檢查類別關係。

## Implementation（super、__init__ 鏈、覆寫與擴充）

### `super()`：呼叫父類別的實作

覆寫方法時，常想「在父類別行為的基礎上加東西」，而非完全取代。用 `super()`：

```python
class Logger:
    def log(self, msg: str) -> None:
        print(f"[LOG] {msg}")

class TimestampLogger(Logger):
    def log(self, msg: str) -> None:
        super().log(f"{msg} @ now")   # 先用父類別的 log，再加時間戳
```

`super()`（3.x 的無參數形式）自動找到 MRO 中「下一個」類別的方法。**在多重繼承下，`super()` 不一定是「字面上的父類別」，而是 MRO 的下一個**（見 [MRO](04-mro.md)）——這是 `super()` 最常被誤解之處。

### `__init__` 的鏈式呼叫

子類別若有自己的 `__init__`，**必須主動呼叫 `super().__init__(...)`** 來初始化父類別的部分，否則父類別的屬性不會被設定：

```python
class Vehicle:
    def __init__(self, wheels: int) -> None:
        self.wheels = wheels

class Car(Vehicle):
    def __init__(self, brand: str) -> None:
        super().__init__(wheels=4)    # 不呼叫的話，self.wheels 不存在！
        self.brand = brand

c = Car("Toyota")
print(c.wheels, c.brand)              # 4 Toyota
```

忘了 `super().__init__()` 是常見 bug——子類別實例會缺少父類別該設的屬性。

### 覆寫 vs 擴充

```python
class Base:
    def process(self) -> list[str]:
        return ["base"]

class Extended(Base):
    def process(self) -> list[str]:
        result = super().process()    # 擴充：保留父類別結果
        result.append("extended")
        return result
```

覆寫是「完全取代」；擴充是「在父類別基礎上加料」（透過 `super()`）。

### 繼承 vs 組合（重要判斷）

繼承不是唯一的重用方式。**組合（composition）**——把其他物件當成自己的屬性——常常更好：

```python
# 繼承：Car is-a Engine？不合理
# 組合：Car has-a Engine（正確）
class Engine:
    def start(self) -> str:
        return "引擎啟動"

class Car:
    def __init__(self) -> None:
        self.engine = Engine()        # 組合：擁有一個 Engine
    def start(self) -> str:
        return self.engine.start()
```

判斷法：**is-a 用繼承（Dog is-a Animal）、has-a 用組合（Car has-a Engine）**。過度用繼承會造成脆弱的深階層與緊耦合；「組合優於繼承」是重要原則（詳見 [mixin 與組合](15-mixin.md)）。

## Code Example（可執行的 Python 範例）

```python
# inheritance_demo.py
class Animal:
    def __init__(self, name: str) -> None:
        self.name = name

    def speak(self) -> str:
        return "..."

    def describe(self) -> str:
        return f"{self.name} says {self.speak()}"


class Dog(Animal):
    def speak(self) -> str:            # 覆寫
        return "Woof"


class GuideDog(Dog):
    def __init__(self, name: str, owner: str) -> None:
        super().__init__(name)         # 鏈式呼叫父類別 __init__
        self.owner = owner

    def describe(self) -> str:
        base = super().describe()      # 擴充父類別方法
        return f"{base}（導盲犬，主人：{self.owner}）"


def demo() -> None:
    d = Dog("Rex")
    print(d.describe())                # Rex says Woof（用覆寫後的 speak）

    g = GuideDog("Buddy", "Alice")
    print(g.describe())                # Buddy says Woof（導盲犬，主人：Alice）

    # isinstance / issubclass
    print(f"g 是 Animal? {isinstance(g, Animal)}")     # True
    print(f"GuideDog 是 Dog 子類? {issubclass(GuideDog, Dog)}")  # True


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python inheritance_demo.py
Rex says Woof
Buddy says Woof（導盲犬，主人：Alice）
g 是 Animal? True
GuideDog 是 Dog 子類? True
```

## Diagram（圖解：繼承與方法解析）

```mermaid
flowchart TD
    Animal[Animal<br/>speak, describe] --> Dog[Dog<br/>覆寫 speak]
    Dog --> GuideDog[GuideDog<br/>擴充 describe]
    Call["g.describe()"] --> GuideDog
    GuideDog -. super . -> Dog
    Dog -. 繼承 describe . -> Animal
    style GuideDog fill:#e8f5e9
```

## Best Practice（最佳實踐）

- **子類別的 `__init__` 一定呼叫 `super().__init__(...)`**，確保父類別部分被正確初始化。
- **擴充而非重寫時用 `super()`**：保留父類別行為再加料。
- **用無參數 `super()`**（3.x），別寫 `super(ClassName, self)`（多餘且易錯）。
- **優先考慮組合**：問「是 is-a 還是 has-a」；has-a 用組合，避免脆弱的深繼承。
- **繼承層級保持淺**：太深的階層難懂難改；需要共享行為時 mixin/組合常更好（見 [mixin](15-mixin.md)）。
- **用 `isinstance` 而非 `type(x) == Cls`**：前者支援子類別（符合 Liskov 替換）。

## Common Mistakes（常見誤解）

- **忘了 `super().__init__()`**：父類別屬性沒被設定，之後存取 AttributeError。
- **以為 `super()` 就是「字面父類別」**：在多重繼承下它是 **MRO 的下一個**，可能不是你以為的類別（見 [MRO](04-mro.md)）。
- **過度使用繼承**：把「有某功能」硬做成繼承（`Car(Engine)`），造成緊耦合；該用組合。
- **繼承層級過深**：五六層的階層難以推理與維護。
- **覆寫時簽章不相容**：子類別方法參數與父類別差太多，破壞 Liskov 替換原則。
- **用 `type(x) == Base` 判型**：對子類別會失敗；用 `isinstance`。

## Interview Notes（面試重點）

- 說得出繼承表達 **is-a**、子類別可**新增/覆寫/擴充**，方法沿 **MRO** 解析。
- 解釋 **`super()`**：呼叫 MRO 中下一個類別的方法；**在多重繼承下不等於字面父類別**。
- 知道**子類別 `__init__` 必須呼叫 `super().__init__()`** 的原因。
- 能講「**繼承 vs 組合**」的判斷（is-a vs has-a）與「組合優於繼承」的理由（降低耦合、避免脆弱階層）。
- 知道用 `isinstance`/`issubclass` 判型，以及 Liskov 替換（子類別應能替代父類別）。

---

➡️ 下一章：[MRO 與多重繼承](04-mro.md)

[⬆️ 回 Part 4 索引](README.md)
