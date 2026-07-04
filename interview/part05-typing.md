# Part 05 面試題:型別系統

> 對應 [Part 05 型別系統](../chapters/05-typing/README.md)。核心:漸進式型別的本質、Optional 誤解、泛型/TypeVar、Protocol、型別窄化。

---

## Q1. Python 的型別註記在執行期會強制嗎?有什麼用?

**考點**:漸進式型別([01-why-type-hints](../chapters/05-typing/01-why-type-hints.md))

**答**:**不強制**。型別註記是 **PEP 484 的漸進式型別**——**執行期預設完全不檢查**(`def f(x: int)` 傳字串也照跑),要靠 **mypy/pyright 等外部工具靜態檢查**。三大價值:**靜態抓錯**(執行前抓型別 bug)、**IDE 支援**(自動完成、跳轉)、**自我說明文件**。

**追問**:

- **靜態檢查 vs 執行期驗證?** → mypy 是**靜態**(不跑程式);**pydantic** 是**執行期**(主動讀註記驗證輸入)。兩者不同。
- **註記存在哪?** → `__annotations__`,是 dataclass/pydantic/FastAPI 的執行期用途。「寫了註記但沒跑檢查器」等於白寫。

---

## Q2.(高頻誤解)`Optional[int]` 是「這參數可以省略」嗎?

**考點**:Optional 誤解([04-optional-union](../chapters/05-typing/04-optional-union.md))

**答**:**不是!** `Optional[X]` **完全等於 `X | None`**——意思是「值可能是 X **或 None**」,**跟「可省略」無關**(可省略靠**預設值**)。

```python
def f(x: Optional[int]):     # x 必須傳,但值可以是 int 或 None
def g(x: int | None = None): # 這個才是「可省略 + 可為 None」
```

**追問**:

- **什麼是型別窄化?** → `is None`/`isinstance`/`assert` 檢查後,mypy 在各分支**自動收斂型別**,不必手動 cast:

```python
def h(x: int | None):
    if x is None: return 0
    return x + 1     # mypy 知道這裡 x 一定是 int
```

- **`if x:` 可以窄化嗎?** → 對可能 falsy 的值(`0`、`""`)會**誤判**(把合法的 0 當成 None),要用 **`is not None`**。現代用 `X | None`(3.10+)勝過 `Optional`。

---

## Q3. `Any` 和 `object` 差在哪?

**考點**:基本註記([02-basic-annotations](../chapters/05-typing/02-basic-annotations.md))

**答**:

- **`Any`**:**關閉型別檢查**——它相容一切、一切相容它,而且會**擴散**(用 Any 的值再傳出去也變不檢查)。是逃生艙,少用。
- **`object`**:**安全但受限**——所有型別的共同基底,但你只能用 object 有的操作(不能直接 `+`、`.foo`),要用前得先 `isinstance` 窄化。

**追問**:

- **容器泛型怎麼寫?** → 3.9+ 用**內建小寫**(`list[int]`、`dict[str, int]`),`typing.List` 已過時(PEP 585)。`Callable` 從 `collections.abc` import。
- **前向參照?** → `from __future__ import annotations`(PEP 563)讓註記延遲評估,能引用還沒定義的型別。

---

## Q4. 什麼是泛型?`TypeVar` 的 `bound` 和 constrained 差在哪?

**考點**:泛型([05-generics-typevar](../chapters/05-typing/05-generics-typevar.md))

**答**:泛型的目的是**保留型別關聯**(輸入輸出型別連動),避免用 `Any` 丟失資訊:

```python
from typing import TypeVar
T = TypeVar("T")
def first(items: list[T]) -> T:    # 回傳型別跟著輸入走
    return items[0]
first([1, 2])      # mypy 知道回 int
first(["a", "b"])  # 知道回 str
```

同一個 TypeVar 多次出現代表**同一型別**。

**bound vs constrained**:

- **`TypeVar("T", bound=Number)`**:**有界**——接受 Number 的**任何子型別**,可用 Number 的方法。
- **`TypeVar("T", int, str)`**:**限定**——只能是**列出的其中之一**(int 或 str,不能是別的)。

**追問**:PEP 695(3.12)新語法 `def f[T](...)` / `class C[T]`,是 TypeVar 的語法糖。TypeVar 是靜態工具,執行期不強制。

---

## Q5. Protocol 和 ABC 差在哪?什麼時候用 Protocol?

**考點**:Protocol([06-protocol](../chapters/05-typing/06-protocol.md))

**答**:**Protocol = 結構化子型別(PEP 544)**——「**長得像就算**」,**不需繼承**,是鴨子型別的型別化。ABC 是**名義子型別**——要**顯式繼承**才算。

```python
from typing import Protocol
class Drawable(Protocol):
    def draw(self) -> None: ...

class Circle:          # 沒繼承 Drawable
    def draw(self): ...
def render(x: Drawable): ...
render(Circle())       # OK!因為 Circle 有 draw(結構相符)
```

**Protocol 適合**:**第三方/既有類別**(你無法改它去繼承你的 ABC,但它結構相符就能用)。

**追問**:`@runtime_checkable` 讓 `isinstance` 可用,但**只檢查方法存在、不檢查簽章**。標準庫有 `SupportsXxx` Protocol(如 `SupportsInt`)。Protocol 預設純靜態,與 ABC 的執行期強制不同。

---

## Q6. mypy 是什麼?`strict` 模式在做什麼?第三方套件沒型別怎麼辦?

**考點**:mypy([07-mypy](../chapters/05-typing/07-mypy.md))

**答**:mypy 是**靜態型別檢查器**(不執行程式),透過**型別推斷 + 註記**驗證型別,把 bug 提前到執行前。

`strict = true` 是**一組嚴格選項**的總開關(尤其 `disallow_untyped_defs`——所有函式都要註記、`no_implicit_optional`)。**漸進導入**:先在少數模組開,用 overrides/ignore_errors 逐步收緊。

**追問**:

- **第三方無型別?** → 裝 **type stub**(`types-requests`),或 `ignore_missing_imports`。
- **抑制錯誤?** → `# type: ignore[error-code]`(帶代碼 + 原因,別裸 ignore);`reveal_type(x)` 除錯用(執行期不存在)。mypy 該進 **CI/pre-commit**。常見錯誤碼:`arg-type`、`union-attr`、`return-value`。

---

## Q7. 註記的最佳實踐?「參數寬、回傳窄」是什麼意思?

**考點**:最佳實踐([08-typing-best-practices](../chapters/05-typing/08-typing-best-practices.md))

**答**:兩大原則:

1. **重點在函式邊界**(公開介面的參數與回傳最該註記,內部區域變數多能推斷)。
2. **參數寬、回傳窄**:**輸入用抽象型別**(`Iterable`/`Mapping`/`Sequence`,接受更多呼叫方)、**輸出用具體型別**(`list`/`dict`,讓呼叫方能用具體操作):

```python
def process(items: Iterable[int]) -> list[int]:   # 收 Iterable、回 list
    return sorted(items)
```

**追問**:避免 `Any`;可變預設用 None;常數用 `Final`;複雜型別取別名;回傳自己用 `Self`。**型別檢查器持續抱怨常反映設計問題**,別硬壓(cast/ignore)。

---

## Q8. `@overload` 和 `cast` 各在什麼時候用?

**考點**:overload/cast/窄化([11-overload-cast-narrowing](../chapters/05-typing/11-overload-cast-narrowing.md))

**答**:

- **`@overload`**:當「**輸入型別決定輸出型別**」時用。規則:多個 `@overload` 簽章(只有簽章、無實作)+ 一個真正實作:

```python
@overload
def get(k: str) -> str: ...
@overload
def get(k: int) -> bytes: ...
def get(k):   # 實際實作
    ...
```

該用 overload,而非回傳一個大 `Union`(讓呼叫方每次都要窄化)。

- **`cast(T, x)`**:告訴 mypy「相信我,這是 T」——**對執行期完全無作用**(不轉換、不檢查),是覆寫 mypy 的**逃生艙**。**應優先用型別窄化**(`isinstance`/`is None`,有執行期保障),cast 是最後手段。

**追問**:`TypeGuard`(3.10+)讓自訂函式能觸發窄化(如 `def is_str_list(x) -> TypeGuard[list[str]]`)。

---

## Q9. `TypedDict`、`Literal`、`Final` 各做什麼?

**考點**:TypedDict/Literal/Final([09-typeddict-literal-final](../chapters/05-typing/09-typeddict-literal-final.md))

**答**:

- **`TypedDict`**:給**固定 key 的 dict** 標結構(`{"name": str, "age": int}`)。**執行期就是普通 dict**,`total=False`/`NotRequired` 控制可選 key。
- **`Literal["a", "b"]`**:限定值只能是**列出的字面值**。
- **`Final`**:標**不可重新賦值的常數**。
- **`Annotated[T, meta]`**:型別 T + 中繼資料(給 pydantic/FastAPI 讀,對 mypy 就是 T)。

**追問**:

- **Literal vs Enum?** → Literal 輕量(值即字面);Enum 有具名成員、可迭代/加方法。
- **TypedDict vs dataclass?** → TypedDict 是 dict 結構(JSON 資料);dataclass 是有方法的物件。全都**靜態檢查、執行期不強制**,要執行期驗證用 pydantic。

---

## Q10. 裝飾器包裝函式後,型別簽章會不見——怎麼保留?`Self` 有什麼用?

**考點**:進階泛型([10-advanced-generics](../chapters/05-typing/10-advanced-generics.md))

**答**:

- **`ParamSpec`(3.10)**:讓裝飾器/包裝函式**保留被包裝函式的完整參數簽章**(`P.args`/`P.kwargs`),否則型別會退化成 `(*args, **kwargs)` 而丟失:

```python
from typing import ParamSpec, TypeVar
P = ParamSpec("P"); R = TypeVar("R")
def logged(f: Callable[P, R]) -> Callable[P, R]:   # 保留 f 的簽章
    @functools.wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return f(*args, **kwargs)
    return wrapper
```

- **`Self`(3.11)**:方法**回傳自己**時用它,讓**子類別得到正確型別**(鏈式呼叫、替代建構子),勝過寫死類別名:

```python
class Builder:
    def add(self, x) -> Self:   # 子類別呼叫時回子類別型別
        ...; return self
```

**追問**:裝飾器要配 `functools.wraps`(保留 metadata)+ `ParamSpec`(保留型別)才完整。各特性最低版本:ParamSpec 3.10、Self 3.11、PEP 695 3.12。

---

⬅️ [Part 04](part04-oop.md) ｜ [索引](README.md) ｜ ➡️ [Part 06 錯誤處理](part06-error-handling.md)
