# Part 04 面試題:物件導向與物件模型

> 對應 [Part 04 OOP](../chapters/04-oop/README.md)。**Python 面試最核心的一 Part**——MRO、`super()`、描述器、metaclass、dataclass 都是高頻題。

---

## Q1. `self` 是什麼?`__init__` 是建構子嗎?

**考點**:class 與實例([01-class-and-instance](../chapters/04-oop/01-class-and-instance.md))

**答**:`self` 是**呼叫方法的那個實例**,Python 自動傳入——`obj.m(x)` 等同 `Cls.m(obj, x)`(`obj` 就是 `self`)。

`__init__` **不是建構子,是初始化器**——物件在它之前就已被 `__new__` 建立好了,`__init__` 只是**初始化**已存在的物件,且**不能回傳值**(回傳非 None 會 TypeError)。真正「建立物件」的是 `__new__`。

**追問**:

- **class 本身是物件嗎?** → 是,`type(C) is type`(class 由 metaclass `type` 建立)。

---

## Q2.(必考)class 屬性和 instance 屬性差在哪?這段的陷阱?

```python
class Dog:
    tricks = []          # class 屬性
    def __init__(self, name): self.name = name

a = Dog("A"); b = Dog("B")
a.tricks.append("sit")
print(b.tricks)
```

**考點**:屬性查找([01-class-and-instance](../chapters/04-oop/01-class-and-instance.md))

**答**:輸出 **`['sit']`**——`b` 也有了!因為 `tricks` 是 **class 屬性,所有實例共用同一個 list**。`a.tricks.append` 改的是那個共享 list。

**查找順序**:instance `__dict__` → class → 父類別。`a.tricks` 找不到 instance 層級的,就找到 class 層級的共享 list。

**正解**:每實例狀態放 `__init__`:

```python
def __init__(self, name):
    self.name = name
    self.tricks = []     # 每實例獨立
```

**規則**:**每實例狀態放 `__init__`、共享常數才放 class 層級**(且別放可變物件)。

**追問**:**`a.tricks = [...]` 呢?** → 那是**賦值遮蔽**,在 `a` 的 instance dict 建一個新屬性,不影響 class 屬性和其他實例。

---

## Q3.(必考)什麼是 MRO?`super()` 呼叫的是字面父類別嗎?

**考點**:MRO 與 C3([04-mro](../chapters/04-oop/04-mro.md))

**答**:**MRO(Method Resolution Order)** 是方法解析順序。Python 3 用 **C3 線性化**,保證:子類別在父類別前、父類別的相對順序保留、每類別只出現一次。

**`super()` 走的是 MRO 中的下一個,不是字面父類別**——在多重繼承(菱形)下,`super()` 可能走到「兄弟」類別:

```python
class A: pass
class B(A):
    def m(self): super().m()   # 這裡 super() 走 MRO,可能到 C 而非 A
class C(A): pass
class D(B, C): pass
# D.__mro__ = [D, B, C, A, object]
# 在 D 實例上,B 的 super() 走到 C!
```

**追問**:

- **為什麼子類 `__init__` 要 `super().__init__()`?** → 讓父類別的初始化被執行;多重繼承下,「全程用 super」才能讓共同祖先的 `__init__` **只執行一次**(協作式繼承)。
- **怎麼查 MRO?** → `Cls.__mro__` 或 `Cls.mro()`。MRO 衝突會在**定義時** TypeError。

---

## Q4. Python 有 private 嗎?`_x`、`__x`、`__x__` 差在哪?

**考點**:封裝([05-encapsulation](../chapters/04-oop/05-encapsulation.md))

**答**:Python **沒有真正的 private/protected**,是「**約定優於強制**」(we're all consenting adults)。三種命名:

- **`_name`**:純**約定**「內部用」,無強制;影響 `import *`。
- **`__name`**:**name mangling**——編譯期改名成 `_ClassName__name`。
- **`__name__`**:dunder,保留給 Python。

**`__name` 的真正目的是避免子類別意外覆蓋,不是保密**——改名讓父類別的 `__x` 變 `_Parent__x`、子類別的變 `_Child__x`,兩者不衝突。你仍能從外部用 `obj._ClassName__name` 存取(所以不是保密)。

**追問**:**要控制存取怎麼辦?** → 用 `@property`(見 Q5),不是靠隱藏;且 Python 不需無腦寫 getter/setter(和 Java 對比)。

---

## Q5. `@property` 有什麼用?為什麼不一開始就寫 getter/setter?

**考點**:property([06-property](../chapters/04-oop/06-property.md))

**答**:`@property` 把**方法偽裝成屬性**。好處:一開始用**公開屬性** `obj.x`,之後要加驗證/計算時,升級成 property **不改變外部介面**(呼叫端還是 `obj.x`)——所以 Python 不需要「預防性地」先寫 getter/setter。

```python
class Temp:
    def __init__(self, c): self._c = c
    @property
    def celsius(self): return self._c
    @celsius.setter
    def celsius(self, v):
        if v < -273.15: raise ValueError("低於絕對零度")
        self._c = v
```

只寫 getter = 唯讀屬性。

**追問**:

- **為何用 `_c` 而不是 `c`?** → property 底層要用**不同名**的屬性存資料,否則 setter 裡 `self.celsius = v` 會**無限遞迴**。
- **昂貴且不變的計算?** → 用 `functools.cached_property`(算一次存起來)。property 本身是**內建的描述器**(見 Q11)。

---

## Q6. `classmethod`、`staticmethod`、實例方法差在哪?classmethod 常拿來幹嘛?

**考點**:方法類型([07-classmethod-staticmethod](../chapters/04-oop/07-classmethod-staticmethod.md))

**答**:

| 類型 | 第一參數 | 能存取 |
|------|----------|--------|
| 實例方法 | `self` | 實例 + 類別 |
| `@classmethod` | `cls` | 類別(不需實例) |
| `@staticmethod` | 無 | 都不能(就是命名空間裡的函式) |

**classmethod 最常當「替代建構子」**(如 `dict.fromkeys`、`datetime.fromisoformat`):

```python
class User:
    def __init__(self, name): self.name = name
    @classmethod
    def from_json(cls, s):
        return cls(json.loads(s)["name"])   # 用 cls 不寫死 User
```

**追問**:**為何用 `cls(...)` 而非寫死 `User(...)`?** → 繼承時 `cls` 綁為**子類別**,`AdminUser.from_json(...)` 會回傳 `AdminUser`(正確型別/多型)。staticmethod 幾乎等同普通函式,價值在命名空間歸屬與可被繼承覆寫。

---

## Q7.(必考)`__repr__` 和 `__str__` 差在哪?

**考點**:dunder 方法([08-dunder-methods](../chapters/04-oop/08-dunder-methods.md))

**答**:

- **`__repr__`**:給**開發者**看——明確、無歧義、理想上可用來重建物件(`eval(repr(x))`);**REPL、容器內、debug** 顯示用。
- **`__str__`**:給**使用者**看——友善可讀;`print()`、`str()` 用。**若沒定義 `__str__`,退回 `__repr__`**。

```python
class Point:
    def __repr__(self): return f"Point(x={self.x}, y={self.y})"   # 開發者
    def __str__(self): return f"({self.x}, {self.y})"             # 使用者
```

**追問**:

- **dunder 是什麼?** → Python 的**協定**:內建操作(`len`/`+`/`==`/`for`/`with`)委派給對應 dunder(`__len__`/`__add__`/`__eq__`/`__iter__`/`__enter__`),這是 Python 多型與鴨子型別的實現。
- **容器協定?** → `__len__`/`__getitem__`/`__iter__`/`__contains__` 讓物件像內建容器;只定義 `__getitem__` 就能讓物件**自動可迭代**。`__call__` 讓實例可呼叫。

---

## Q8.(必考)`@dataclass` 做什麼?可變預設值怎麼寫?frozen 有什麼用?

**考點**:dataclass([09-dataclass](../chapters/04-oop/09-dataclass.md))

**答**:`@dataclass`(3.7+)**自動產生 `__init__`/`__repr__`/`__eq__`**,靠**型別註記**辨識欄位,大減樣板。

**可變預設值必須用 `field(default_factory=...)`**(直接寫 `= []` 會觸發[可變預設參數陷阱](part02-fundamentals.md#q3必考這段程式碼的輸出為什麼),dataclass 會直接報錯保護你):

```python
from dataclasses import dataclass, field
@dataclass
class Cart:
    items: list = field(default_factory=list)   # 不能寫 = []
```

**`frozen=True`**:不可變 + 自動 `__hash__`(能當 dict key / 放 set);非 frozen 預設**不可 hash**。

**追問**:

- **其他選項?** → `order=True`(依欄位產生比較方法)、`__post_init__`(驗證/衍生欄位)、`field(init=False)`。
- **dataclass vs NamedTuple vs pydantic?** → dataclass(可變/不可變、標準庫)、NamedTuple(不可變、tuple 相容)、pydantic(執行期驗證,見 [Part 14](part14-web.md))。有預設的欄位不能排在無預設之前。

---

## Q9. ABC 和 Protocol 差在哪?

**考點**:抽象基底類別([10-abc](../chapters/04-oop/10-abc.md))

**答**:兩者都定義「介面」,但機制不同:

- **ABC(`abc.ABC` + `@abstractmethod`)**:**名義子型別**——要**顯式繼承**;沒實作抽象方法就**無法實例化**(錯誤提前到建立物件時);執行期強制。
- **Protocol(`typing.Protocol`)**:**結構化子型別(鴨子型別)**——**不需繼承**,只要**有對的方法**就算符合;主要給 [mypy 靜態檢查](part05-typing.md)。

```python
from abc import ABC, abstractmethod
class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...   # 子類別沒實作就不能實例化
```

**追問**:**`collections.abc`?** → 提供內建 ABC(`Iterable`/`Sequence`/`Mapping`…)供 isinstance 與繼承。ABC 可同時有抽象和具體方法(模板方法模式)。

---

## Q10. 物件建立分哪兩步?什麼時候需要 `__new__`?

**考點**:`__new__` vs `__init__`([12-new-and-init](../chapters/04-oop/12-new-and-init.md))

**答**:兩步:

1. **`__new__(cls, ...)`**:**建立**並回傳實例(第一參數 `cls`)。
2. **`__init__(self, ...)`**:**初始化**已建立的實例(第一參數 `self`,不回傳)。`__init__` 只在 `__new__` 回傳 cls 實例時才被呼叫。

**需要 `__new__` 的場景**:**子類化不可變型別**(值必須在建立時定,如繼承 `int`/`tuple`/`str`)、**單例**、物件池/快取。

**追問**:**單例用 `__new__` 的陷阱?** → 即使 `__new__` 回傳同一個實例,**`__init__` 仍會每次被呼叫**(可能重複初始化),要防護。

---

## Q11. 什麼是描述器?為什麼說「方法本身就是描述器」?

**考點**:描述器協定([11-descriptors](../chapters/04-oop/11-descriptors.md))

**答**:**描述器**是實作了 `__get__`/`__set__`/`__delete__` 的類別屬性,讓「屬性存取邏輯可重用」。

- **data descriptor**(有 `__set__`/`__delete__`):**優先於** instance `__dict__`。
- **non-data descriptor**(只有 `__get__`):**低於** instance `__dict__`。
- 完整查找順序:data descriptor → instance `__dict__` → non-data descriptor / class 屬性。

**關鍵洞察**:`property`、**方法**、`classmethod`/`staticmethod` **全是描述器**。方法是 non-data descriptor——透過實例存取時 `__get__` 把 `self` 綁進去產生 **bound method**,這就解釋了「方法為何自帶 self」;property 是 data descriptor,所以能攔截屬性存取。

**追問**:

- **`__set_name__`?** → 3.6+,描述器自動取得它被賦值的屬性名。
- **經典陷阱?** → 描述器是**類別屬性、所有實例共用一份**,每實例狀態要存到 **obj 上**(用 `__set_name__` 拿到的名字存進 `obj.__dict__`),別存在描述器自己身上。

---

## Q12. metaclass 是什麼?什麼時候真的需要它?

**考點**:metaclass([13-metaclass](../chapters/04-oop/13-metaclass.md))

**答**:核心關係:**實例由 class 建立、class 由 metaclass 建立**(預設是 `type`)。因為 **class 也是物件**,`type(Dog)` 是 `type`。`class` 敘述其實是**呼叫 metaclass 的語法糖**——`type(name, bases, namespace)` 能動態造 class。

**真實應用**:ABC(ABCMeta)、ORM(Django/SQLAlchemy 的 Model)、Enum——**宣告式框架**的底層,在 class **定義時**介入(如自動註冊、驗證欄位)。

**關鍵判斷**:**大多數情況不需要 metaclass**——`__init_subclass__` 和**類別裝飾器**是更輕量的替代。Tim Peters 名言:「如果你不確定需不需要 metaclass,那就是不需要。」

**追問**:多重繼承的 metaclass 要相容,否則衝突。

---

## Q13. Enum 有什麼好處?`Enum` 和 `IntEnum` 差在哪?

**考點**:Enum([14-enum](../chapters/04-oop/14-enum.md))

**答**:Enum 用**具名常數取代魔術值**——型別安全、可讀、可迭代、IDE 支援;成員是**單例**(可用 `is` 比較)。成員有 `name`/`value`,可用 `Color(value)`/`Color[name]` 反查。

- **`Enum`**:**型別隔離**——成員 **不等於**原值(`Color.RED != 1`),避免誤用。
- **`IntEnum`/`StrEnum`**:成員「**是**」int/str,可與原生型別比較/運算——用於**相容**(如需要當 int 傳給舊 API)。

**追問**:`auto()`(自動賦值)、`@unique`(防重複)、`Flag`(位元組合)。相同 value 的成員會變**別名**。

---

## Q14. 「組合優於繼承」是什麼意思?什麼是 mixin?

**考點**:mixin 與組合([15-mixin](../chapters/04-oop/15-mixin.md))

**答**:**繼承綁定實作、緊耦合、脆弱基底、深階層難懂;組合封裝好、彈性、可執行期抽換行為**——所以優先組合。用 **is-a(繼承)vs has-a(組合)** 判斷:狗 is-a 動物(繼承),車 has-a 引擎(組合)。

**mixin**:聚焦**單一能力**、不獨立使用、透過多重繼承混入的類別。命名 `XxxMixin`、**放繼承列表最前面**(因 MRO 順序,才能覆寫/擴充後面的類別)。

**追問**:

- **「繼承 list 加方法」的壞處?** → 會**洩漏** list 的所有原方法(使用者能用你不想暴露的操作);組合(內含一個 list 屬性)才能只暴露你要的介面。
- **要執行期抽換行為?** → 組合 + 策略模式(連結依賴注入)。

---

## Q15. 屬性查找失敗時會發生什麼?`__getattr__` 和 `__getattribute__` 差在哪?

**考點**:屬性存取([02-attributes-and-methods](../chapters/04-oop/02-attributes-and-methods.md))

**答**:屬性存在 `__dict__`(`self.x = v` 即 `self.__dict__['x'] = v`,所以能動態增刪屬性)。查找順序:instance `__dict__` → class/父類別(含描述器)→ **`__getattr__` 兜底** → AttributeError。

- **`__getattr__`**:**只在正常查找失敗時**呼叫——適合做「動態/代理屬性」的兜底。
- **`__getattribute__`**:**每次**屬性存取都呼叫(攔截一切)——強大但危險(容易無限遞迴、拖慢),很少直接用。

**追問**:`getattr`/`setattr`/`hasattr`/`delattr` 動態存取;動態屬性是雙面刃(打錯字不報錯,靜態檢查抓不到)。

---

⬅️ [Part 03](part03-data-structures.md) ｜ [索引](README.md) ｜ ➡️ [Part 05 型別系統](part05-typing.md)
