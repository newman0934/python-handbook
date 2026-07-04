# Part 10 面試題:CPython 內部與記憶體

> 對應 [Part 10 CPython 內部](../chapters/10-cpython-internals/README.md)。深挖底層——引用計數、GC、bytecode、GIL 內部、interning,是進階/資深職位的高頻題。

---

## Q1. 「Python 一切皆物件」是什麼意思?

**考點**:一切皆物件([01-everything-is-object](../chapters/10-cpython-internals/01-everything-is-object.md))

**答**:數字、字串、函式、類別、模組、**型別本身**全是堆積上的物件,都有 **id/type/value**、可被當值操作(對比 Java 的 primitive/Object 二分)。連**型別也是物件**——`int` 是 `type` 的實例、`type(type) is type`,這是 metaclass 與動態性的基礎。兩個根:**`object`**(所有類別的基底)、**`type`**(所有類別的型別)。

**追問**:

- **這解釋了哪些特性?** → 一等公民函式、運算子多載、內省、動態建類、統一記憶體管理。
- **代價?** → 「整數也是完整物件」有開銷(int ~28B),純 Python 數值運算慢 → 需 numpy 向量化。

---

## Q2. 物件的三要素?`isinstance` 和 `type()` 差在哪?

**考點**:物件模型([02-object-model](../chapters/10-cpython-internals/02-object-model.md))

**答**:三要素 **id / type / value**,對應 `is`(比 id)、`==`(比 value)、`isinstance`/`type()`(查 type)。

**`isinstance` vs `type()`**:

- **`isinstance(x, Cls)`**:**相容**——包含子類、符合多型(`isinstance(True, int)` 是 True,因 bool 是 int 子類)。
- **`type(x) == Cls`**:**精確**——排除子類。

**幾乎總用 `isinstance`**(除非你真的要排除子類)。

**追問**:id 在 CPython 是**記憶體位址**(實作細節),生命週期內唯一不變,但**物件回收後 id 可能被重用**。`is` vs `==` 見 [Part 02 Q4](part02-fundamentals.md#q4-is-和--差在哪什麼時候用哪個)。

---

## Q3.(必考)CPython 怎麼管理記憶體?引用計數的死角是什麼?

**考點**:引用計數 + GC([03-reference-counting](../chapters/10-cpython-internals/03-reference-counting.md) / [04-garbage-collection](../chapters/10-cpython-internals/04-garbage-collection.md))

**答**:**兩道防線**:

1. **引用計數(主力、即時)**:每個物件記「有幾個引用指向它」——賦值/存容器/傳參 +1,重綁/`del`/離開作用域 −1,**歸零立刻回收**。
2. **循環 GC(補充)**:處理引用計數的**死角——循環引用**。

**死角:循環引用**——A 引用 B、B 引用 A,即使外部都不再用,兩者的引用計數**永遠 ≥ 1、不會歸零**,引用計數回收不了。所以需要額外的**循環 GC** 來偵測並回收這種垃圾:

```python
a = {}; b = {}
a["b"] = b; b["a"] = a   # 循環引用!引用計數回收不了,靠循環 GC
```

**追問**:

- **循環 GC 怎麼運作?** → **分代**(三代,基於「弱世代假說:多數物件短命」,頻繁掃年輕代),**觸發基於分配數**(非定時,故循環垃圾非即時回收),**只追蹤容器型物件**(int/str 不參與循環)。
- **怎麼避免/打破循環?** → 用 `weakref`(見 Q9)。`gc` 模組可 `collect()`/`disable()`/調閾值。

---

## Q4.(必考)引用計數和 GIL 有什麼關係?

**考點**:GIL 內部([08-gil-internals](../chapters/10-cpython-internals/08-gil-internals.md))

**答**:**引用計數是 GIL 存在的根本原因**。引用計數的 +1/−1 **不是原子操作**,多執行緒同時改同一物件的計數會**競態損毀**(計數錯誤 → 提早釋放或記憶體洩漏 → 崩潰)。

CPython 的選擇:用**一把大鎖(GIL)** 保護所有計數,而非為每個物件加細粒度鎖——**更簡單、單執行緒更快、C 擴充好寫**(是取捨)。

**為何移除 GIL 難**:引用計數要改成執行緒安全(拖慢單執行緒)、C 擴充相容性、記憶體管理複雜化——PEP 703(free-threaded)才在可接受取捨下實現。

**追問**:完整因果鏈:**引用計數(需保護)→ GIL(保護計數)→ 在 PVM 層一次一執行緒跑 bytecode → 並發策略(CPU 用多行程)**。GIL 只保證單一 bytecode 原子,`+=` 仍需鎖。

---

## Q5. 什麼是 bytecode?怎麼看?為什麼 `LOAD_FAST` 比 `LOAD_GLOBAL` 快?

**考點**:bytecode/dis([06-bytecode-and-dis](../chapters/10-cpython-internals/06-bytecode-and-dis.md))

**答**:bytecode 是原始碼**編譯後的低階中間指令**,存在 code object、由 PVM 執行、快取成 `.pyc`。它是**堆疊導向**的(推值/彈值/運算)。用 `dis.dis` 反組譯:

```python
import dis
dis.dis(lambda x: x + 1)
#   LOAD_FAST   x          ← 讀區域變數(快)
#   LOAD_CONST  1
#   BINARY_OP   +
#   RETURN_VALUE
```

**`LOAD_FAST`(區域變數)比 `LOAD_GLOBAL`(全域)快**:區域變數存在陣列裡按索引直取;全域要查 dict。這是「把常用的全域搬成區域」優化的原理。

**追問**:編譯期有**常數摺疊**(`1+2*3` 編譯時就算成 7);bytecode 是 **CPython 實作細節、隨版本變**(3.11 大改),別寫死依賴。`dis` 揭露「推導式 vs for+append」「join vs +=」為何有效能差。

---

## Q6. 什麼是 PVM?為什麼 Python 比 C 慢?

**考點**:PVM([07-pvm](../chapters/10-cpython-internals/07-pvm.md))

**答**:**PVM(Python Virtual Machine)** 是 CPython 的 bytecode 直譯器——一個**取指令-執行迴圈**、**堆疊機器**(用求值堆疊),逐條執行 bytecode。

**Python 為何比 C 慢**:三個開銷疊加——

1. **直譯開銷**:每條 bytecode 要取指令/解碼/分派(C 是直接跑機器碼)。
2. **動態型別**:執行期才查型別、找方法。
3. **物件層開銷**:連整數都是完整物件(見 Q1)。

**追問**:**frame** 是每次函式呼叫的執行狀態(區域變數/求值堆疊/位置);**呼叫堆疊 = frame 疊**,traceback 和 `RecursionError` 都源於此。PVM 是 CPython 實作,**PyPy 用 JIT**(編熱點成機器碼)快很多——加速方向是 C 擴充、向量化、JIT。

---

## Q7. CPython 怎麼配置記憶體?為什麼長跑服務記憶體降不下來?

**考點**:記憶體管理([05-memory-management](../chapters/10-cpython-internals/05-memory-management.md))

**答**:**分層**:小物件(≤512B)由 **pymalloc**(arena → pool → block)管理,減少系統呼叫;大物件直接 `malloc`。

**記憶體不一定還給 OS**:pymalloc **保留 block 供重用**,加上碎片化使 arena 還不掉——這解釋了「長跑服務即使釋放了物件,記憶體用量也不降回去」。

**追問**:

- **物件開銷?** → 每物件有引用計數 + 型別指標等固定開銷(int ~28B),這是純數值運算慢的根源,故用 numpy 向量化。`getsizeof` 是**淺層**的(不含內部元素)。
- **減少記憶體?** → `__slots__`(省 instance dict)、numpy/array、生成器。用 `tracemalloc` 除錯記憶體。

---

## Q8. 什麼是 interning?為什麼 `a = 256; a is 256` 是 True 但 `257` 可能是 False?

**考點**:interning([09-interning](../chapters/10-cpython-internals/09-interning.md))

**答**:**interning(駐留)** 是 CPython **快取重用不可變物件**的優化——**小整數(−5 到 256)** 預先建好共用、常見字串駐留。相同值共用同一物件,所以 `is` 為 True:

```python
a = 256; b = 256; a is b   # True(小整數快取範圍內)
a = 257; b = 257; a is b   # 可能 False(超出範圍,各建各的)
```

**這正是「別用 `is` 比數字/字串值」的實作根源**——範圍內 True、範圍外 False,依實作而定。**比值一律用 `==`,`is` 只用於單例(`None`)**。

**追問**:小整數範圍是 **−5~256**(最常用);字串駐留規則模糊(字面值駐留、動態產生通常不駐留),可用 `sys.intern` 主動駐留(大量重複字串省記憶體)。是 CPython 實作細節,別依賴。

---

## Q9. weakref(弱引用)是什麼?什麼時候用?

**考點**:weakref([10-weakref](../chapters/10-cpython-internals/10-weakref.md))

**答**:**弱引用**指向物件但**不增加引用計數**,所以**不阻止物件被回收**;物件回收後弱引用失效(`ref()` 回 `None`)。

**主要用途**:

- **快取(`WeakValueDictionary`)**:避免快取本身阻止物件回收 → 防記憶體洩漏。
- **打破循環引用**:父子互指時,子對父用弱引用(否則循環)。
- **觀察者模式**:持有觀察者但不延長其壽命。

**追問**:不是所有物件可弱引用(`int`/`str`/`tuple` 不行);`weakref.finalize` 比 `__del__` 可靠,但重要清理仍用 `with`。弱引用的本質是「**持有參照卻不延長壽命**」,用於解決引用計數/循環引用的實際問題。

---

## Q10. Python 3.11 為什麼變快很多?什麼是適應性直譯器?

**考點**:適應性直譯器([11-adaptive-interpreter](../chapters/10-cpython-internals/11-adaptive-interpreter.md))

**答**:**PEP 659 適應性專用直譯器(3.11)**——**觀察執行**,把**熱點的通用指令「專用化」** 成快速版本(如偵測到某加法一直是 int,就換成 int 專用加法,省去型別檢查),型別變了安全退回。**不是 JIT,是更聰明的直譯**。

加上零成本例外(強化 EAFP)、更輕的函式呼叫/frame,**3.11+ 比 3.10 快 10–60%**(Faster CPython 計畫)。

**追問**:

- **有 JIT 嗎?** → **3.13 引入實驗性 JIT**(copy-and-patch)——CPython 朝有 JIT 演進。
- **對我有什麼好處?** → **升級版本就免費加速**;型別一致的熱點受益最大。但極致效能仍需 numpy/C。**適應性直譯 + free-threaded + JIT** 是 CPython 近年最大的演進,談得出來代表跟上生態。

---

⬅️ [Part 09](part09-concurrency.md) ｜ [索引](README.md) ｜ ➡️ [Part 11 標準庫](part11-stdlib.md)
