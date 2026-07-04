# Part 06 面試題:錯誤處理

> 對應 [Part 06 錯誤處理](../chapters/06-error-handling/README.md)。核心:try/except/else/finally、例外鏈、context manager、EAFP、assert 陷阱。

---

## Q1. `try/except/else/finally` 四個區塊各做什麼?

**考點**:try 結構([02-try-except](../chapters/06-error-handling/02-try-except.md))

**答**:

- **`try`**:放可能出錯的程式。
- **`except`**:處理特定例外(由上而下匹配)。
- **`else`**:`try` **沒出錯**才執行——把「成功後邏輯」和「可能出錯的程式」分離,**縮小 try 範圍、避免誤接不相關例外**。
- **`finally`**:**一定執行**(含 return/break/例外時),用於清理。

```python
try:
    f = open(path)
except FileNotFoundError:
    ...
else:
    data = f.read()   # 只在 open 成功時
finally:
    f.close()         # 一定清理
```

**追問**:

- **except 順序?** → 由上而下匹配,**子類別要放前面**(否則被父類別先接走)。
- **finally 的陷阱?** → 別在 finally 裡 `return`(會蓋掉 try 的 return/例外)。資源清理**優先用 `with`**。

---

## Q2. `raise` 有哪幾種形式?什麼時候該拋例外、什麼時候回傳錯誤值?

**考點**:raise([03-raise](../chapters/06-error-handling/03-raise.md))

**答**:三形式:

- **`raise Error(msg)`**:拋一個新例外。
- **單獨 `raise`**:在 except 內**重新拋出**(保留原 traceback)。**注意 `raise e` 會重設 traceback**,重新拋要用單獨 `raise`。
- **`raise X from Y`**:串接原因(例外鏈,見 Q4)。

**該拋還是回傳?**:呼叫端該修正的**異常**情況 → 拋例外;**預期內的「沒有」** → 回傳 None。經典對比:`d[key]`(找不到拋 `KeyError`)vs `d.get(key)`(找不到回 None)。

**追問**:不該用例外做一般流程控制;guard clause 儘早檢查;拋出要型別對 + 訊息含上下文。

---

## Q3. 自訂例外要繼承什麼?為什麼建議設計「基底例外 + 具體子類」?

**考點**:自訂例外([04-custom-exceptions](../chapters/06-error-handling/04-custom-exceptions.md))

**答**:繼承 **`Exception`**(不是 `BaseException`),以 `Error` 結尾命名。

**基底 + 具體子類的價值**:呼叫端可**彈性選擇粒度**——`except MyLibError`(一次接住整個函式庫的錯)或 `except SpecificError`(精準處理)。函式庫慣例會提供一個頂層例外:

```python
class OrderError(Exception): ...              # 基底
class OutOfStockError(OrderError): ...         # 具體
class PaymentFailedError(OrderError): ...
# 呼叫端:except OrderError(全接)或 except OutOfStockError(精準)
```

**追問**:**攜帶結構化資料**(屬性)優於解析訊息字串,要 `super().__init__(message)`。is-a 真的成立時可繼承具體內建例外(如 `NegativeValueError(ValueError)`)。

---

## Q4. 什麼是例外鏈?`raise X from e` 和在 except 裡直接 raise 差在哪?

**考點**:例外鏈([05-exception-chaining](../chapters/06-error-handling/05-exception-chaining.md))

**答**:例外鏈的目的是**轉換例外時保留根本原因**,讓 traceback 顯示完整因果。兩種:

- **顯式鏈 `raise X from e`**:設 `__cause__`,traceback 顯示 **"The above exception was the direct cause..."**。
- **隱式鏈**:在 except 內直接 `raise Y`(沒 from),設 `__context__`,顯示 **"During handling of the above exception..."**。

```python
try:
    data = json.loads(s)
except json.JSONDecodeError as e:
    raise ConfigError("設定檔格式錯誤") from e   # 保留原因
```

**追問**:

- **`from None`?** → 抑制原因(謹慎用,會藏資訊)。
- **反模式?** → `raise X(str(e))`——遺失了原例外的型別與 traceback。轉換例外的慣例是明確 `raise X from e`。

---

## Q5. `with` 背後是什麼協定?`__exit__` 回傳 `True` 會怎樣?

**考點**:context manager([06-context-manager](../chapters/06-error-handling/06-context-manager.md))

**答**:`with` 依賴 **context manager 協定 `__enter__`/`__exit__`**,等價於**保證執行的 try/finally**。`__enter__` 的回傳值綁給 `as`;**`__exit__` 無論正常或例外都會被呼叫**(清理保證)。

**關鍵考點**:`__exit__` **回傳 `True` 會「吞掉」例外**(例外不再往上傳);回傳 falsy(含 None)則**讓例外傳播**。預設應回 falsy(別默默吞例外)。

```python
class Managed:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        cleanup()
        return False   # 讓例外正常傳播
```

**追問**:`__exit__` 收到 `(exc_type, exc_val, exc_tb)`,正常離開時皆為 None。資源管理優先用 `with`。

---

## Q6. 怎麼用 generator 寫 context manager?有什麼陷阱?

**考點**:contextlib([07-contextlib](../chapters/06-error-handling/07-contextlib.md))

**答**:用 `@contextmanager` + generator——`yield` **前**是 enter、**後**是 exit,`yield` 的值綁給 `as`:

```python
from contextlib import contextmanager
@contextmanager
def timer():
    start = time.perf_counter()
    try:
        yield                          # 這裡是 with 區塊
    finally:
        print(time.perf_counter() - start)   # 必須放 finally!
```

**關鍵陷阱**:**必須用 `try/finally` 包住 `yield`**,否則 with 區塊內拋例外時,`yield` 後的清理**不會執行**。

**追問**:其他 contextlib 工具——`suppress`(優雅忽略特定例外,勝過 try/except/pass)、`ExitStack`(動態管理不定數量資源)、`closing`、`nullcontext`。generator 寫法簡潔,類別寫法適合攜狀態/複雜情境。

---

## Q7. EAFP 和 LBYL 差在哪?為什麼 Python 偏好 EAFP?

**考點**:EAFP vs LBYL([09-eafp-vs-lbyl](../chapters/06-error-handling/09-eafp-vs-lbyl.md))

**答**:

- **EAFP**(Easier to Ask Forgiveness than Permission):**先做,失敗再處理**(try/except)。
- **LBYL**(Look Before You Leap):**先檢查再做**(if)。

**Python 偏好 EAFP**,不只是風格——關鍵技術理由是**避免 TOCTOU 競態條件**(Time-Of-Check to Time-Of-Use):

```python
# LBYL:有競態!檢查完到使用之間,檔案可能被刪
if os.path.exists(path):
    open(path)          # 這瞬間檔案可能已不存在
# EAFP:沒有競態
try:
    open(path)
except FileNotFoundError:
    ...
```

**追問**:

- **例外很慢所以該避開?** → 迷思。**例外只在拋出時有成本**,成功路徑幾乎零開銷。
- **何時 LBYL 較好?** → 失敗頻繁(例外成本累積)、失敗有難回復的副作用、簡單邊界檢查。`dict.get`/`getattr(默認)` 是內建的 EAFP 封裝。

---

## Q8.(必考)為什麼裸 `except:` 危險?`except Exception` 有什麼不同?

**考點**:例外階層([10-exception-hierarchy](../chapters/06-error-handling/10-exception-hierarchy.md))

**答**:例外樹的根是 **`BaseException`**;`Exception` 是「一般錯誤」的基底。但 **`SystemExit`、`KeyboardInterrupt`、`GeneratorExit` 直接繼承 `BaseException`、不在 `Exception` 下**。

裸 `except:` 接住 **`BaseException`**——會**接住 Ctrl-C(`KeyboardInterrupt`)和退出(`SystemExit`)**,讓你的程式無法被中斷/正常退出!`except Exception` **刻意放過**這些控制訊號,只接一般錯誤。

```python
try: ...
except:              # 危險!Ctrl-C 也被吞
    ...
except Exception:    # 正確:只接一般錯誤,放過 Ctrl-C
    ...
```

**追問**:

- **`except Exception: pass` 呢?** → **吞錯反模式**——錯誤消失無蹤,debug 惡夢。要記錄用 `log.exception()`,要忽略特定例外用 `contextlib.suppress`。
- **捕捉父類別?** → 接住所有子類別(`except OSError` 接 `FileNotFoundError`),所以「具體在前」。

---

## Q9. `ExceptionGroup` 和 `except*` 是什麼?什麼時候用?

**考點**:例外群組([11-exception-groups](../chapters/06-error-handling/11-exception-groups.md))

**答**:`ExceptionGroup`(3.11 / PEP 654)用於「**同時發生多個獨立錯誤**」——把它們打包一起拋,主要為 **asyncio `TaskGroup`** 的結構化並發而生(多個 task 各自可能失敗)。

用 **`except*`** 處理——關鍵差異:**`except*` 可能觸發多個分支**(群組裡有幾種型別就觸發幾個),每個分支拿到只含匹配例外的子群組:

```python
try:
    ...  # 可能拋 ExceptionGroup
except* ValueError as eg:      # 處理群組中所有 ValueError
    ...
except* TypeError as eg:       # 也可能同時觸發這個
    ...
```

**追問**:`except*` **不能與 `except` 混用**、需 3.11+;一般場景不需要,主要用於並發/批次的「多錯並發」。

---

## Q10.(必考)`assert` 有什麼陷阱?什麼時候不該用?

**考點**:assert([12-assert-warnings-traceback](../chapters/06-error-handling/12-assert-warnings-traceback.md))

**答**:**`python -O`(最佳化模式)會移除所有 assert**!所以 assert **只能用於內部假設/開發期抓 bug**,**絕不能用於輸入驗證或安全檢查**——那些一旦被 `-O` 移除就形同虛設(安全漏洞)。輸入/安全檢查要用 `raise`:

```python
assert user.is_admin        # 危險!-O 下這行消失,權限檢查失效
if not user.is_admin:       # 正確
    raise PermissionError
```

**另一個陷阱**:`assert (cond, msg)` **加括號**變成 assert 一個**非空 tuple → 恆為真**(永遠通過,失去檢查作用)。正確是 `assert cond, msg`(不加括號)。

**追問**:

- **assert / warnings / raise / traceback 各定位?** → assert(內部假設)、warnings(非致命提醒如棄用)、raise(錯誤)、traceback(記錄回溯)。
- **traceback 怎麼讀?** → **由下往上讀**,最底行是真正的例外;記錄用 `log.exception()`(自動含 traceback)。

---

## Q11. Python 用例外還是錯誤碼處理錯誤?好處是什麼?

**考點**:例外機制([01-exceptions](../chapters/06-error-handling/01-exceptions.md))

**答**:用**例外**。拋出後**沿呼叫堆疊往上傳播**,被某層的 `try/except` 接住,或**終止程式並印 traceback**。好處:**可在合適層級集中處理**,不必每層都檢查回傳值(對比 C 的錯誤碼要層層傳遞、容易忘記檢查)。

例外是**物件**(繼承 `Exception`),帶 `args`/訊息。常見內建:`ValueError`(值不對)、`TypeError`(型別不對)、`KeyError`(dict 缺 key)、`IndexError`(索引越界)、`FileNotFoundError` 等。

**追問**:「不處理就崩潰」是**特性**(強迫正視錯誤),不該用裸 except 或吞例外掩蓋。

---

## Q12. 錯誤處理的最佳實踐有哪些?

**考點**:最佳實踐([08-error-handling-best-practices](../chapters/06-error-handling/08-error-handling-best-practices.md))

**答**:核心原則:

1. **精確捕捉**:接具體例外,別裸 `except:` 或籠統 `except Exception`(除非真要兜底並記錄)。
2. **不吞錯**:別 `except: pass`;記錄用 `log.exception()`。
3. **在對的層級處理**:能處理才接,不能處理就往上拋。
4. **讓 bug 崩潰**:捕捉**預期內可恢復**的錯,**讓非預期的 bug 崩潰**(才會被發現修正)。
5. **轉換例外用 `raise ... from`**、**資源用 `with`**、**忽略用 `suppress`**。

**追問**:「捕捉預期內可恢復的錯、讓非預期 bug 崩潰」是判斷核心——過度捕捉會把真 bug 藏起來。

---

⬅️ [Part 05](part05-typing.md) ｜ [索引](README.md) ｜ ➡️ [Part 07 迭代器與生成器](part07-iterators-generators.md)
