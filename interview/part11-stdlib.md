# Part 11 面試題:標準庫

> 對應 [Part 11 標準庫](../chapters/11-stdlib/README.md)。挑面試常問的:datetime 時區、JSON/pickle 安全、subprocess 注入、random vs secrets、logging。

---

## Q1.(必考)naive 和 aware datetime 差在哪?`datetime.now()` 有什麼陷阱?

**考點**:datetime([03-datetime](../chapters/11-stdlib/03-datetime.md))

**答**:

- **naive**:**無時區資訊**——有歧義(「3 點」是哪個時區的 3 點?)、不能與 aware 混用比較。
- **aware**:**帶時區**(tzinfo)。

**黃金原則**:**內部一律用 aware UTC 儲存/運算,只在顯示時轉當地時間**。

**`datetime.now()` 的陷阱**:回傳 **naive 的本地時間**!要 aware UTC 用 `datetime.now(timezone.utc)`:

```python
from datetime import datetime, timezone
datetime.now()               # naive!有歧義
datetime.now(timezone.utc)   # aware UTC ✓
```

**追問**:具名時區/DST 用 **`zoneinfo.ZoneInfo`(3.9+)**(取代 pytz),`astimezone` 轉時區;程式間交換用 **ISO 8601**(`isoformat`/`fromisoformat`);`replace(tzinfo=)` 只標記不轉換(轉換用 `astimezone`)。

---

## Q2.(必考)JSON 和 pickle 差在哪?為什麼外部資料不能用 pickle?

**考點**:JSON/pickle 安全([04-json](../chapters/11-stdlib/04-json.md) / [12-pickle](../chapters/11-stdlib/12-pickle.md))

**答**:

| | JSON | pickle |
|---|------|--------|
| 型別 | 基本型別 | 幾乎任何 Python 物件 |
| 安全 | **安全**(不執行程式碼) | **危險** |
| 跨語言 | ✓ | Python 專屬 |
| 格式 | 文字 | 二進位 |

**關鍵安全點**:**`pickle.loads` 反序列化不可信資料會執行任意程式碼**(透過 `__reduce__`,攻擊者可構造惡意 pickle 執行 `os.system`)!所以**絕不 pickle 不可信來源**,對外資料一律用 **JSON**。pickle 只適合「完全可信的內部資料 + 需存複雜物件」(快取、狀態)。

**追問**:

- **JSON 型別陷阱?** → **tuple 序列化後讀回變 list**、非字串 key 被轉字串、set/bytes/datetime 不支援(用 `default`)。中文用 `ensure_ascii=False`。
- **pickle 其他缺點?** → 版本相容性弱、不能 pickle lambda。

---

## Q3.(必考)`subprocess` 怎麼用?為什麼不能 `shell=True` 拼使用者輸入?

**考點**:subprocess([07-subprocess](../chapters/11-stdlib/07-subprocess.md))

**答**:`subprocess.run` 是現代介面,**args 傳引數列表**(`["ls", "-l", path]`)而非字串。

**命令注入**:**絕不用 `shell=True` 拼接使用者輸入**——會被 shell 解析執行惡意命令:

```python
subprocess.run(f"ls {user_input}", shell=True)   # 危險!user_input="; rm -rf /"
subprocess.run(["ls", user_input])                # 安全!引數不經 shell
```

引數列表**不經 shell**,`user_input` 只會被當一個引數(即使含 `;` 也不會被執行)。

**追問**:常用參數 `capture_output=True`、`text=True`、`check=True`(失敗拋 `CalledProcessError`)、`timeout`。**能用純 Python(shutil/pathlib)就別呼叫外部命令**;舊的 `os.system` 該淘汰。

---

## Q4.(高頻安全)`random` 能用來產生密碼/token 嗎?

**考點**:random vs secrets([11-random-math-statistics](../chapters/11-stdlib/11-random-math-statistics.md))

**答**:**不能!** `random` 是**偽亂數**(可預測,知道 seed 或觀察足夠輸出就能推算),**不可用於密碼學**。安全隨機(密碼、token、密鑰、session id)一律用 **`secrets`**:

```python
import secrets
secrets.token_hex(16)       # 安全的隨機 token
secrets.token_urlsafe(32)   # URL 安全的
# random.randint(...) 產密碼 = 安全漏洞!
```

**追問**:`random` 用於**非安全**場景(模擬、抽樣、洗牌);`random.seed()` 用於**重現**(測試)。`math` 是浮點(比較用 `isclose`);`statistics` 適合小資料(大資料用 numpy),`stdev`(樣本 n−1)vs `pstdev`(母體 n)。

---

## Q5. `re.search`、`re.match`、`re.fullmatch` 差在哪?什麼是 ReDoS?

**考點**:re([05-re](../chapters/11-stdlib/05-re.md))

**答**:

- **`search`**:在**任何位置**找到就算(找東西用)。
- **`match`**:只從**開頭**匹配。
- **`fullmatch`**:**整個字串**都要符合(驗證格式用)。

pattern 一律用 **raw string**(`r"\d+"`)避免反斜線衝突。

**ReDoS(災難性回溯)**:某些 pattern(巢狀量詞如 `(a+)+`)遇到特定輸入會**指數級回溯**,拖垮 CPU——對**不可信輸入**的 regex 要謹慎(安全風險)。

**追問**:群組 `(...)`、具名群組 `(?P<name>...)`、`sub` 替換(`\1` 引用)、`re.compile` 快取。**能用字串方法就別用 regex**(可讀性)。Match 可能是 None,取 group 前要檢查。

---

## Q6. 為什麼要用 logging 而非 print?

**考點**:logging([08-logging](../chapters/11-stdlib/08-logging.md))

**答**:logging **可分級**(DEBUG/INFO/WARNING/ERROR/CRITICAL)、**可設門檻開關**(正式環境設 INFO 以上)、**含脈絡**(時間/模組/等級)、**可導向多目的地**(檔案/集中收集)。print 全都做不到。

核心概念:**Logger**(每模組 `getLogger(__name__)`)、**Level**(門檻)、**Handler**(送到哪)、**Formatter**(格式)。

**追問**:

- **except 裡怎麼記?** → `logger.exception(...)`(自動含 traceback)。
- **函式庫該 basicConfig 嗎?** → **不該**(讓使用者控制設定);用 `%s` 佔位(延遲格式化省效能);正式服務用**結構化(JSON)日誌**利於集中收集。

---

## Q7. `os` 和 `sys` 各管什麼?`pathlib` 為什麼取代 `os.path`?

**考點**:os/sys/pathlib([01-os-sys](../chapters/11-stdlib/01-os-sys.md) / [02-pathlib](../chapters/11-stdlib/02-pathlib.md))

**答**:

- **`os`**:**作業系統**——環境變數(`os.environ`)、行程、檔案系統。
- **`sys`**:**直譯器**——`argv`、`exit`、`path`、`stdout/stderr`。

**`pathlib.Path` 取代 `os.path` 字串操作**:物件導向、用 `/` 組路徑、**自動跨平台**(分隔符):

```python
from pathlib import Path
config = Path(__file__).parent / "config.toml"   # 定位相對腳本(別依賴 cwd)
config.read_text(encoding="utf-8")
```

**追問**:環境變數是 **12-factor 的設定方式**(密鑰不寫死,可選用 `.get`、必填用 `[]`);`sys.exit(code)` 實為拋 `SystemExit`(繼承 `BaseException`,`except Exception` 不攔);錯誤訊息寫 **stderr**。

---

## Q8. `requests` 有什麼一定要注意的?async 程式能用嗎?

**考點**:HTTP client([14-http-client](../chapters/11-stdlib/14-http-client.md))

**答**:

- **每個請求一定設 `timeout`**——否則對方不回會**永遠掛住**:`requests.get(url, timeout=5)`。
- **`requests` 預設不因錯誤狀態碼拋例外**——要 `resp.raise_for_status()` 或手動檢查(4xx/5xx 不會自動拋)。
- **async 程式別用 requests**(它是**阻塞**的,會卡住 event loop,見 [Part 09](part09-concurrency.md#q11必考在-async-函式裡呼叫-timesleep5-或-requestsget-會怎樣)),用 **`httpx`**。

**追問**:選擇——同步用 `requests`(最成熟)、async 用 `httpx`;用 `Session` 重用連線;POST 用 `json=`;處理 `Timeout`/`ConnectionError`/`RequestException`。

---

## Q9. TCP 和 UDP 差在哪?`recv` 有什麼要注意?

**考點**:socket([15-socket](../chapters/11-stdlib/15-socket.md))

**答**:socket 是網路通訊的**底層端點**(requests/Web 框架/asyncio 都建在它之上)。

- **TCP**:可靠、有連線、有序(檔案傳輸、HTTP)。
- **UDP**:快、無連線、不保證送達(串流、遊戲、DNS)。

**`recv` 不保證完整訊息**——TCP 是**位元組串流**,一次 `recv` 可能只收到訊息的一部分(或多個訊息黏在一起),**要自己處理訊息邊界**(長度前綴或分隔符)。socket 收發 **bytes**(要 encode/decode)。

**追問**:伺服器 `bind→listen→accept`、客戶端 `connect`。日常該用高階工具,理解 socket 是為了懂底層與除錯;多客戶端需並發(threading/asyncio)。

---

## Q10. `argparse` 怎麼做 CLI?布林旗標怎麼處理?

**考點**:argparse([10-argparse](../chapters/11-stdlib/10-argparse.md))

**答**:`argparse` 是標準庫做 CLI 的正解(處理型別轉換、驗證、`--help`、錯誤),取代手動解析 `sys.argv`:

```python
parser = argparse.ArgumentParser()
parser.add_argument("path")                          # 位置引數(必填)
parser.add_argument("--count", type=int, default=1)  # 選用 + 轉型
parser.add_argument("--verbose", action="store_true")  # 布林旗標
```

**布林旗標用 `action="store_true"` 而非 `type=bool`**——`type=bool("false")` 是 True(非空字串皆真)的陷阱!

**追問**:位置引數(必填)vs 選用引數(`--`,可預設);`choices=`(限值)、`nargs`(多值)、`add_subparsers`(子命令);所有引數預設是字串(要 `type=`)。現代替代 click/typer,但 argparse 是標準庫。

---

## Q11. 檔案 I/O 有什麼最佳實踐?大檔怎麼讀?

**考點**:io([06-io](../chapters/11-stdlib/06-io.md))

**答**:

- **一律 `with open(...)`** 保證關檔(context manager 清理)。
- **文字模式指定 `encoding="utf-8"`**(跨平台),二進位模式(`b`)處理 bytes。
- **大檔逐行迭代**(惰性省記憶體),別全載:

```python
with open("huge.log", encoding="utf-8") as f:
    for line in f:            # 惰性,一次一行,記憶體恆定
        process(line)
    # 別用 f.read()/f.readlines() 全載入
```

**追問**:模式 `r`/`w`/`a`/`x`(+`b`),`w` 會覆蓋;`io.StringIO`/`BytesIO` 是記憶體中的檔案(測試、餵檔案介面 API);小檔可用 `Path.read_text()`。

---

## Q12. 設定檔該用什麼格式?YAML 有什麼安全問題?

**考點**:設定格式([13-csv-config-tomllib](../chapters/11-stdlib/13-csv-config-tomllib.md))

**答**:依用途選:

| 用途 | 格式 |
|------|------|
| 應用設定 | **TOML**(`tomllib` 3.11+,有型別、支援註解) |
| API/資料交換 | JSON |
| 密鑰/部署 | 環境變數 |
| 老專案 | INI(configparser) |

**YAML 安全**:**用 `yaml.safe_load` 而非 `yaml.load`**——後者不安全(能執行任意物件建構,類似 pickle 的風險)。

**追問**:`tomllib` **只讀**(二進位模式,寫用 tomli-w);CSV 用 `csv` 模組別自己 split(正確處理引號/逗號/換行),`DictReader`/`DictWriter` 以欄位名存取,開檔加 `newline=""`。

---

⬅️ [Part 10](part10-cpython-internals.md) ｜ [索引](README.md) ｜ ➡️ [Part 12 測試](part12-testing.md)
