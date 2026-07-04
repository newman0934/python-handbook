# Part 03 面試題:資料結構

> 對應 [Part 03 資料結構](../chapters/03-data-structures/README.md)。核心考點:底層結構與複雜度、可變性/hashable、深淺複製、排序與 heapq/bisect。

---

## Q1. list 底層是什麼?各操作的時間複雜度?

**考點**:動態陣列([01-list](../chapters/03-data-structures/01-list.md))

**答**:list 底層是**動態陣列**(連續的物件指標)。複雜度:

| 操作 | 複雜度 |
|------|--------|
| 索引 `a[i]` | O(1) |
| 尾端 `append`/`pop()` | O(1) 攤銷 |
| 頭部/中間 `insert`/`pop(0)` | O(n)(要搬移後面所有元素) |
| `x in a` / `.index(x)` | O(n)(線性掃描) |

尾端 append 攤銷 O(1) 靠 **over-allocation**(容量用完時一次多配一些,不必每次都搬)。

**追問**:

- **頭部頻繁進出怎麼辦?** → 用 `collections.deque`(兩端 O(1))。
- **頻繁成員檢查?** → 用 `set`(O(1) vs list 的 O(n))。
- **`append` vs `extend`?** → `append(x)` 加一個元素;`extend(xs)` 逐個加入 iterable 的元素(`append([1,2])` 是加入一個 list,`extend([1,2])` 是加兩個數)。

---

## Q2.(必考)`grid = [[0]*3]*2; grid[0][0]=1` 之後 grid 是什麼?

**考點**:list 別名陷阱([01-list](../chapters/03-data-structures/01-list.md))

**答**:`[[1,0,0], [1,0,0]]`——**兩列都變了**!

**原因**:`[[0]*3]*2` 的外層 `*2` 是**重複同一個 inner list 的參照**,兩列指向**同一個** list。改 `grid[0][0]` 等於改那個共享的 list。

**正解**用推導式(每列建新 list):

```python
grid = [[0]*3 for _ in range(2)]   # 各列獨立
grid[0][0] = 1                     # [[1,0,0], [0,0,0]] ✓
```

**追問**:**為什麼 `[0]*3` 沒事?** → 因為 `0` 是不可變的,`*3` 複製參照沒差(你只能替換不能改 `0`);問題出在外層複製了**可變的 list** 參照。

---

## Q3. tuple 是不可變的,那 `t = (1, [2, 3]); t[1].append(4)` 會怎樣?

**考點**:tuple 含可變元素([02-tuple](../chapters/03-data-structures/02-tuple.md))

**答**:**成功**,`t` 變成 `(1, [2, 3, 4])`!

tuple 的「不可變」指的是**它裝的參照不能換**(不能 `t[1] = ...`),但**參照指向的物件若可變,仍能被原地修改**。所以 `t[1].append(4)` 改的是那個 list,不是 tuple 本身。

**後果**:這個 tuple **不再可 hash**——含有可變元素,不能當 dict key / 放 set:

```python
{(1, [2]): "x"}   # TypeError: unhashable type: 'list'
```

**追問**:

- **逗號的重要性?** → **逗號才構成 tuple**,不是括號。單元素要 `(x,)`(沒逗號 `(x)` 只是括號)。
- **何時升級 NamedTuple/dataclass?** → 需要欄位命名、可讀性時。多回傳值本質就是 tuple + 解構。

---

## Q4. dict 底層是什麼?保證有序嗎?

**考點**:雜湊表([04-dict](../chapters/03-data-structures/04-dict.md))

**答**:dict 底層是**雜湊表**,查找/插入/刪除**平均 O(1)**。key 必須 **hashable**(要能算 hash 定位)。

**順序**:**Python 3.7 起「保證」保留插入順序**(3.6 是 CPython 實作細節、未列入規範)。這個時間點常被考。

**追問**:

- **計數/分組怎麼寫最 Pythonic?** → 計數用 `collections.Counter`;分組用 `defaultdict(list)`;取值給預設用 `d.get(k, default)`;`setdefault` 也行但會**預先求值預設物件**(有副作用時要注意)。
- **遍歷中改大小?** → keys/values/items 是**動態視圖**,遍歷時改變 dict 大小會 `RuntimeError`。
- **dict 有多核心?** → 物件屬性 `__dict__`、`**kwargs`、模組命名空間全是 dict。

---

## Q5. 判斷元素在不在集合裡,為什麼 set 比 list 快?去重要保序怎麼做?

**考點**:set([05-set-frozenset](../chapters/03-data-structures/05-set-frozenset.md))

**答**:set 底層是**雜湊表(只有 key)**,成員檢查 `x in s` **平均 O(1)**;list 是線性掃描 **O(n)**。大量查找一定用 set。

**去重保序**:set **不保證順序**,若要「去重又保留原順序」,用 `dict.fromkeys`(dict 3.7+ 保序):

```python
list(dict.fromkeys([3, 1, 3, 2, 1]))   # [3, 1, 2] ← 去重且保序
list(set([3, 1, 3, 2, 1]))             # 順序不保證
```

**追問**:

- **集合運算?** → `|`(聯集)`&`(交集)`-`(差集)`^`(對稱差)。**運算子需兩邊皆 set,方法(`.union` 等)接受任意 iterable**。
- **空 set 怎麼寫?** → `set()`(`{}` 是空 dict!)。
- **frozenset?** → 不可變、**可 hash**,能當 dict key / set 元素。

---

## Q6.(必考)自訂類別覆寫 `__eq__` 後放進 set 會怎樣?

**考點**:hashable 契約([07-hashable](../chapters/03-data-structures/07-hashable.md))

**答**:**只定義 `__eq__` 會讓 `__hash__` 變成 `None`**,物件變**不可 hash**,放進 set / 當 dict key 會報 `TypeError: unhashable type`。

**原因**:Python 規定 **`a == b ⟹ hash(a) == hash(b)`**(相等的物件 hash 必須相同)。你改了 `__eq__` 卻沒改 `__hash__`,兩者可能不一致,所以 Python 乾脆把 `__hash__` 設 None 防止你誤用。

**補救**:同時定義 `__hash__`(用決定相等的欄位組 tuple 來 hash),或用 `@dataclass(frozen=True)`(自動產生一致的 `__eq__`+`__hash__`):

```python
class Point:
    def __init__(self, x, y): self.x, self.y = x, y
    def __eq__(self, o): return (self.x, self.y) == (o.x, o.y)
    def __hash__(self): return hash((self.x, self.y))   # 用相同欄位
```

**追問**:

- **為何可變物件不可 hash?** → 內容變 → hash 變 → 在雜湊表裡「失聯」(找不回原位置)。所以 hashable 要求 hash 穩定。

---

## Q7. 淺複製和深複製差在哪?

**考點**:複製層次([09-copy-shallow-deep](../chapters/03-data-structures/09-copy-shallow-deep.md))

**答**:三個層次:

- **賦值(`b = a`)**:別名,同一物件。
- **淺複製(`a.copy()`/`a[:]`/`list(a)`/`copy.copy`)**:**新外層 + 共用內層**——改內層的可變物件會互相影響。
- **深複製(`copy.deepcopy`)**:**遞迴複製到底**,完全獨立;能處理循環參照,但較慢。

```python
import copy
a = [[1, 2], [3, 4]]
b = a.copy()          # 淺複製
b[0].append(9)        # 改內層 list
print(a)              # [[1, 2, 9], [3, 4]] ← a 的內層也變了!
c = copy.deepcopy(a)  # 深複製,c 改內層不影響 a
```

**追問**:

- **為何一層(不可變元素)淺複製就等效獨立?** → 內層是不可變的,你只能**替換**(換綁,不影響原物件)不能**原地改**,所以淺複製就夠。
- **怎麼從根本避免複製煩惱?** → 用**不可變結構**(tuple/frozenset/frozen dataclass)。

---

## Q8. `sorted` 和 `list.sort` 差在哪?Python 用什麼排序演算法?

**考點**:排序([11-sorting](../chapters/03-data-structures/11-sorting.md))

**答**:`sorted(iterable)` 回**新 list**、接受任何 iterable;`list.sort()` **原地排序、回 `None`**、只能用在 list。

Python 用 **Timsort**:O(n log n)、**穩定排序**(相等元素保持原相對順序)。

**穩定性的用途**:**分次排序實現多鍵**——先按次要鍵排、再按主要鍵排,穩定性保證次要鍵順序在主要鍵相等時被保留。

**追問**:

- **多鍵排序怎麼寫?** → 用 tuple key:`sorted(data, key=lambda x: (x.dept, -x.salary))`(部門升冪、薪水降冪);或 `operator.itemgetter`/`attrgetter`(比 lambda 快且清楚)。
- **常見陷阱?** → `x = a.sort()` 讓 `x` 是 `None`(sort 回 None)!要新 list 用 `sorted`。
- **只要前 k 大?** → 用 `heapq.nlargest(k, data)`(O(n log k))勝過全排序 O(n log n)。

---

## Q9. `heapq` 是什麼?怎麼做優先佇列?怎麼做 max-heap?

**考點**:heapq([12-heapq-bisect](../chapters/03-data-structures/12-heapq-bisect.md))

**答**:`heapq` 是 **min-heap**:`heap[0]` 是最小值 O(1),`heappush`/`heappop` O(log n),`heapify` O(n)。

- **max-heap**:Python 沒有,用**負號**模擬(`heappush(h, -x)`,取出再取負)。
- **優先佇列**:push `(priority, tiebreaker, item)` 的 tuple——中間放**序號**打破平手,避免當 priority 相同時去比較 item 本身(item 可能不可比較而報錯)。

```python
import heapq, itertools
counter = itertools.count()
pq = []
heapq.heappush(pq, (priority, next(counter), task))
```

**追問**:

- **top-k?** → `heapq.nlargest(k, data)` / `nsmallest`,O(n log k);`heapq.merge` 合併多個有序串流。
- **應用?** → Dijkstra、Top-K、合併 K 個有序串列——都是 heapq 的白板題。

---

## Q10. `bisect` 做什麼?`bisect_left` 和 `bisect_right` 差在哪?

**考點**:bisect([12-heapq-bisect](../chapters/03-data-structures/12-heapq-bisect.md))

**答**:`bisect` 在**已排序**序列上做二分搜尋找插入位置(O(log n))。

- `bisect_left(a, x)`:回「**小於 x** 的元素個數」(x 插在相等元素**左邊**)。
- `bisect_right(a, x)`:回「**小於等於 x** 的元素個數」(插在相等元素**右邊**)。

用途:分級(成績→等第)、範圍計數、維持有序插入:

```python
import bisect
grades = [60, 70, 80, 90]
letters = "FDCBA"
letters[bisect.bisect(grades, score)]   # 依分數落點取等第
```

**追問**:**`insort` 的成本?** → `bisect.insort` 找位置 O(log n) 但**插入是 O(n)**(list 要搬移)。前提是序列**必須已排序**。

---

## Q11. `collections` 模組有哪些好用工具?

**考點**:collections([08-collections-module](../chapters/03-data-structures/08-collections-module.md))

**答**:

- **`Counter`**:計數(`Counter(words)`)、`most_common(k)`、多重集合算術。
- **`defaultdict`**:缺 key 自動建預設(`defaultdict(list)` 做分組)。**注意讀取缺失 key 會建立它**(副作用)。
- **`deque`**:兩端 O(1)(BFS、滑動視窗、`maxlen` 環形緩衝)。
- **`namedtuple`**:具名 tuple、不可變、`_replace` 產生新物件。

**追問**:

- **`defaultdict` vs `setdefault` vs `Counter` 計數怎麼選?** → 純計數用 `Counter`;分組成 list/set 用 `defaultdict`;偶爾補預設用 `setdefault`。
- **加分工具?** → `ChainMap`(多層命名空間查找)、`OrderedDict`(3.7 後多被普通 dict 取代,但保留 `move_to_end` 等方法)。

---

## Q12. 切片 `a[start:stop:step]` 的語意?`a[::-1]` 和 `a[:]` 各是什麼?

**考點**:切片([03-slicing](../chapters/03-data-structures/03-slicing.md))

**答**:**半開區間**(含 start、不含 stop),支援負索引、負步長、省略參數,且**不越界**(超出範圍不報錯)。

- **`a[::-1]`**:step=-1 → **反轉**。
- **`a[:]`**:**淺複製**整個序列(新物件)。
- 切片產生**新物件**(淺複製),成本 O(k)。

**追問**:

- **切片賦值的差別?** → `a[i:j] = x`(原地替換一段);`a[:] = x`(**原地整批替換**,會影響所有別名);`a = x`(換綁,別名不受影響)。
- **限制?** → 切片賦值只適用**可變序列**(list);tuple/str 不行(不可變)。

---

⬅️ [Part 02](part02-fundamentals.md) ｜ [索引](README.md) ｜ ➡️ [Part 04 OOP](part04-oop.md)
