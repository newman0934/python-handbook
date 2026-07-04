# Part 02 面試題:語言基礎

> 對應 [Part 02 語言基礎](../chapters/02-fundamentals/README.md)。這一 Part 是**面試高頻重災區**——可變預設參數、傳參語意、閉包陷阱、`is` vs `==` 幾乎必考。

---

## Q1. Python 的變數是什麼?`a = [1,2]; b = a` 之後改 `b` 會影響 `a` 嗎?

**考點**:名稱綁定與別名([01-dynamic-typing](../chapters/02-fundamentals/01-dynamic-typing.md))

**答**:Python 的變數是**「名稱綁定到物件」,不是盒子裝值**。`a = [1,2]` 是讓名稱 `a` 指向一個 list 物件;`b = a` 讓 `b` 指向**同一個**物件(別名 aliasing)。所以:

```python
a = [1, 2]
b = a
b.append(3)      # 原地修改同一個 list
print(a)         # [1, 2, 3] ← a 也變了!
print(a is b)    # True(同一物件)
```

因為 `b.append` 是**原地修改**那個共享的 list。若要避免,用複製:`b = a.copy()` 或 `b = list(a)`。

**追問**:

- **`b = a` 後 `b = [9]` 會影響 a 嗎?** → 不會。那是**重新賦值(換綁)**,`b` 改指向新物件,`a` 仍指原物件。**重新賦值 vs 原地修改**是理解一切的關鍵。
- **動態 vs 強型別?** → Python 是**動態型別**(名稱可換綁不同型別)**+ 強型別**(不自動轉型,`"1" + 1` 報錯)。兩組正交概念。

---

## Q2. Python 的參數傳遞是傳值還是傳參考?

**考點**:傳參語意,必考([08-functions](../chapters/02-fundamentals/08-functions.md))

**答**:都不是,是 **call by object reference(傳物件參考 / 傳共享)**。函式收到的是**引數物件的參考**。結果取決於物件可不可變、以及你是**重新賦值**還是**原地修改**:

```python
def f(x):
    x = x + 1        # 重新賦值 → 換綁到新物件,不影響外部
def g(lst):
    lst.append(9)    # 原地修改 → 改到同一物件,影響外部

n = 1; f(n); print(n)          # 1(不可變 int,換綁不影響外部)
items = [1]; g(items); print(items)  # [1, 9](可變 list,原地改影響外部)
```

**規則**:對**不可變**物件(int/str/tuple),函式內「修改」其實是換綁,不影響外部;對**可變**物件(list/dict/set),原地修改會影響外部。

**追問**:

- **怎麼避免函式改到外部物件?** → 進函式先**複製**(`lst = lst.copy()`),或**回傳新物件**而非原地改。
- **函式沒 return 回傳什麼?** → `None`。多回傳值本質是 **tuple + 解構**(`return a, b` 回 tuple)。

---

## Q3.(必考)這段程式碼的輸出?為什麼?

```python
def add(item, target=[]):
    target.append(item)
    return target

print(add(1))
print(add(2))
```

**考點**:可變預設參數([09-parameters-args-kwargs](../chapters/02-fundamentals/09-parameters-args-kwargs.md))

**答**:輸出 `[1]` 然後 **`[1, 2]`**(不是 `[2]`)!

**原因**:**預設值在函式定義時求值「一次」**,那個 list 物件被**所有呼叫共用**。第一次呼叫 append 進去、第二次又 append 進**同一個** list,所以累積。

**正解**:用 `None` 哨兵:

```python
def add(item, target=None):
    if target is None:
        target = []       # 每次呼叫都建新 list
    target.append(item)
    return target
```

**追問**:

- **為什麼只求值一次?** → 因為 `def` 執行時就把預設值算好綁在函式物件上(`add.__defaults__`),之後每次呼叫共用。
- **哪些預設值安全?** → 不可變的(`None`、數字、字串、tuple)。**任何可變預設值都是地雷**。

---

## Q4. `is` 和 `==` 差在哪?什麼時候用哪個?

**考點**:身分 vs 相等,必考([05-operators](../chapters/02-fundamentals/05-operators.md))

**答**:`is` 比**身分**(是不是同一個物件,比的是 `id()`);`==` 比**值相等**(呼叫 `__eq__`)。

- **判斷 `None`/單例用 `is`**:`x is None`——快、身分比較、不被 `__eq__` 覆寫誤導。
- **判斷值相等用 `==`**:`x == 5`、`s == "hi"`。
- **絕不用 `is` 比數字/字串的值**:`a == 1000` 對,`a is 1000` 錯——小整數快取、字串 interning 都是**實作細節**,不可依賴。

```python
a = [1, 2]; b = [1, 2]
a == b   # True(值相等)
a is b   # False(不同物件)
```

**追問**:

- **`is` 能覆寫嗎?** → 不能,`is` 是內建身分比較,無法多載;`==` 可透過 `__eq__` 覆寫。
- **運算子是什麼?** → **方法呼叫的語法糖**:`a + b` → `a.__add__(b)`,這是運算子多載的基礎。

---

## Q5.(必考)這個迴圈的輸出?怎麼修?

```python
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])
```

**考點**:閉包迴圈捕捉陷阱([12-closures](../chapters/02-fundamentals/12-closures.md))

**答**:輸出 **`[2, 2, 2]`**(不是 `[0, 1, 2]`)!

**原因**:閉包**捕捉的是變數 `i` 本身,不是當下的值**。所有 lambda 都指向同一個 `i`,迴圈結束後 `i` 是最終值 `2`,所以三個都回傳 2。

**兩種修正**:

```python
# 1. 用預設參數在定義時「凍結」當下的值
funcs = [lambda i=i: i for i in range(3)]   # → [0, 1, 2]

# 2. 工廠函式(每次建立新的作用域)
def make(i):
    return lambda: i
funcs = [make(i) for i in range(3)]          # → [0, 1, 2]
```

**追問**:

- **什麼是閉包?** → 巢狀函式 + 引用外層變數 + 回傳內層;**外層函式返回後,被捕捉的變數仍存活**(存在 `__closure__` 的 cell 裡)。
- **閉包怎麼保持可變狀態?** → 用 `nonlocal`(如計數器)。**裝飾器就建立在閉包之上**。

---

## Q6.(必考)這段為什麼報 `UnboundLocalError`?

```python
x = 10
def f():
    print(x)
    x = 20
f()
```

**考點**:LEGB 與作用域([11-scope-legb](../chapters/02-fundamentals/11-scope-legb.md))

**答**:報錯,因為 **函式內對 `x` 有賦值(`x = 20`),Python 就把整個函式裡的 `x` 視為區域變數**。於是 `print(x)` 時區域 `x` 還沒被賦值 → `UnboundLocalError`。

**規則**:**賦值使名稱變區域**(不管賦值在哪一行)。名稱查找順序是 **LEGB**:Local → Enclosing → Global → Built-in。

**修法**:

```python
def f():
    global x        # 宣告要改模組層級的 x
    print(x)
    x = 20
```

**追問**:

- **`global` vs `nonlocal`?** → `global` 改**模組層級**變數;`nonlocal` 改**最近外層函式**的變數(用於閉包)。
- **哪些結構建立作用域?** → 函式、類別、模組、推導式;**`for`/`if`/`while` 不建立作用域**(迴圈變數會外洩)。

---

## Q7.(必考)`0.1 + 0.2 == 0.3` 是 True 嗎?為什麼?怎麼正確比較?

**考點**:浮點精度([15-float-precision-decimal](../chapters/02-fundamentals/15-float-precision-decimal.md))

**答**:**False**!`0.1 + 0.2` 實際是 `0.30000000000000004`。

**根因**:浮點用 **IEEE 754 二進位**表示,某些十進位小數(如 0.1)**無法用二進位精確表示**,只能近似——這是**所有**浮點語言共通的,不是 Python bug。

**正確比較**:`math.isclose(0.1 + 0.2, 0.3)` → True。

**追問**:

- **金額怎麼處理?** → 用 **`Decimal`**,且**必須用字串建立**(`Decimal("0.1")`,用 float 建會帶入誤差),搭配 `quantize` + 明確 `rounding` 做財務捨入。
- **三者取捨?** → `float`(快、近似)、`Decimal`(十進位精確、財務)、`Fraction`(分數完全精確)。`Decimal` 與 `float` 不能直接混算(TypeError)。

---

## Q8. `and`/`or` 的短路求值是什麼?`x or default` 有什麼陷阱?

**考點**:布林與短路([03-booleans-and-none](../chapters/02-fundamentals/03-booleans-and-none.md))

**答**:`and`/`or` **短路求值**且**回傳運算元本身**(不是純 bool):`a or b` 若 `a` 為真回 `a`,否則回 `b`;`a and b` 若 `a` 為假回 `a`,否則回 `b`。

`x or default` 的陷阱:當 `x` 是**合法的 falsy 值**(`0`、`""`、`[]`)時,會被誤判而用了 default:

```python
def greet(name):
    name = name or "訪客"   # 若 name="" 會變訪客(可能沒問題)
count = user_input or 10      # 若 user_input=0 會變 10!(0 是合法輸入卻被覆蓋)
```

要判「有沒有給值」用 `if x is None` 而非 `or`。

**追問**:

- **falsy 值有哪些?** → `False`、`None`、`0/0.0/0j`、空字串/序列/dict/set、`__bool__` 或 `__len__` 為零的物件;其餘皆真。
- **`bool` 和 `int` 的關係?** → `bool` 是 `int` 的**子類別**,`True==1`、`False==0`,可參與算術(`sum(bool(x) for x in xs)` 計數)。

---

## Q9. list 推導式和生成器表達式差在哪?何時用哪個?

**考點**:推導式([13-comprehensions](../chapters/02-fundamentals/13-comprehensions.md))

**答**:`[x for x in xs]` 是 **list 推導式**——**立即**建好整個 list、佔記憶體;`(x for x in xs)` 是**生成器表達式**——**惰性**、逐個產生、幾乎不佔記憶體。

- 要**多次使用/需索引/需長度** → list 推導式。
- 只**遍歷一次、資料量大/無限** → 生成器(省記憶體)。

```python
sum(x*x for x in range(10**6))   # 生成器:不建百萬元素的 list,省記憶體
```

**追問**:

- **推導式為什麼比 `for`+`append` 快?** → 省去重複的屬性查找(`list.append`)與函式呼叫,由直譯器最佳化。
- **`(...)` 是 tuple 嗎?** → **不是**,是生成器!tuple 沒有推導式語法,要 tuple 用 `tuple(x for x in xs)`。
- **迴圈變數會外洩嗎?** → 不會,**推導式有獨立作用域**(Python 3)。

---

## Q10. `for...else` 的 `else` 什麼時候執行?

**考點**:控制流([06-control-flow](../chapters/02-fundamentals/06-control-flow.md))

**答**:`else` 在迴圈**未被 `break` 中斷、正常跑完**時執行;若被 `break` 就**不**執行。典型用於搜尋——「找到就 break,沒找到(正常結束)就走 else」:

```python
for x in items:
    if x == target:
        print("找到")
        break
else:
    print("找不到")   # 只有沒 break(沒找到)才執行
```

**追問**:

- **Python 有 switch 嗎?** → 沒有 C 式 switch;用 `if/elif` 或 3.10 的 `match`。
- **`for` 是計數迴圈嗎?** → 不是,是**遍歷可迭代物件**(背後是迭代器協定)。取索引用 `enumerate`,平行遍歷用 `zip`(加 `strict=True` 防長度不一)。

---

## Q11. `match` 是 Python 版的 switch 嗎?有什麼陷阱?

**考點**:結構化模式比對([07-match-statement](../chapters/02-fundamentals/07-match-statement.md))

**答**:**不是 switch**。`match`(3.10 / PEP 634)是**結構化模式比對**——比對值的**結構**,並在成功時**解構綁定**變數。能匹配字面值、序列 `[a, *rest]`、對映 `{"k": v}`、類別 `Point(x=0)`、or `|`、guard `if`。

**必答陷阱**:**裸名稱是「捕捉」,永遠成功並綁定**,不是比對常數:

```python
STATUS = 200
match code:
    case STATUS:      # 陷阱!這是捕捉,把 code 綁到 STATUS,永遠命中
        ...
    case 200:         # 正確:字面值才是比對
        ...
```

要比對具名常數,用**帶點名稱**(`case http.OK`)或字面值。

**追問**:

- **序列模式匹配 str 嗎?** → **不匹配** str/bytes(刻意設計,避免把字串當字元序列)。
- **`case _`?** → 萬用分支;case 順序要 **specific → general**。

---

## Q12. `str` 和 `bytes` 差在哪?什麼是 `UnicodeDecodeError`?

**考點**:編碼([16-encoding-bytes](../chapters/02-fundamentals/16-encoding-bytes.md))

**答**:`str` 是 **Unicode 文字**(碼位序列),`bytes` 是**原始位元組**。Python 3 **嚴格分離**、需明確 `encode`(str→bytes)/`decode`(bytes→str)。**編碼**是「碼位→位元組」的規則,同字串不同編碼產生不同位元組(Unicode 是**字元集**,不是編碼)。

`UnicodeDecodeError` 的成因:**用錯編碼 decode**(如用 latin-1 去 decode 一段 UTF-8)。修法:用資料**真正的編碼**(通常 UTF-8)decode。

**追問**:

- **Unicode 三明治?** → **邊界 decode/encode、內部只用 str**(輸入立刻 decode 成 str、輸出前才 encode 成 bytes)。
- **為何首選 UTF-8?** → 變長、相容 ASCII、無 BOM/大小端問題。開檔要**明確指定 `encoding="utf-8"`**(別依賴平台預設,Windows 主控台是 cp950 的坑)。

---

## Q13. `int` 會溢位嗎?`-7 // 2` 等於多少?

**考點**:數字([02-numbers](../chapters/02-fundamentals/02-numbers.md))

**答**:Python `int` 是**任意精度、不會溢位**(要多大就多大,自動擴充),不像 C 的固定寬度整數。

`-7 // 2 == -4`(不是 -3)!因為 `//` 是**地板除法(向下取整)**,-3.5 向下取整是 -4。而 `/` 是**真除法回 float**(`-7 / 2 == -3.5`)。

**追問**:

- **`round(2.5)`?** → `2`(不是 3)!`round` 用**銀行家捨入**(四捨六入五成雙);`int()` 是**截斷**(向零)。
- **`divmod`?** → 同時回商和餘 `divmod(7, 2) == (3, 1)`。混合運算會**向上升型**(int + float → float)。

---

## Q14. `:=`(海象運算子)是什麼?什麼場景用?

**考點**:賦值運算式([14-walrus-operator](../chapters/02-fundamentals/14-walrus-operator.md))

**答**:`:=`(3.8 / PEP 572)是**賦值運算式**——**賦值的同時回傳該值**,可嵌入運算式中;而 `=` 是敘述、沒有值。主要場景:

```python
# while 讀取迴圈去重複
while (line := f.readline()):
    process(line)

# if + 保留計算結果(避免算兩次)
if (n := len(data)) > 10:
    print(f"太長:{n}")

# 推導式避免重算
[y for x in data if (y := f(x)) > 0]
```

**追問**:

- **為何 Python 原本禁止 `if x = 5`?** → 防 `=`/`==` 誤植的經典 bug;`:=` 用不同符號**刻意**補上這能力。
- **有什麼要注意?** → 優先順序常需**加括號**;推導式中的 `:=` 綁定會**洩漏到外層作用域**(和一般推導式變數不同)。是可讀性雙面刃,別濫用。

---

⬅️ [回面試題庫索引](README.md) ｜ ➡️ [Part 03 資料結構](part03-data-structures.md)
