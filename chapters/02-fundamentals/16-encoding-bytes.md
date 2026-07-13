# 字元編碼與 bytes/str

> `UnicodeDecodeError` 大概是每個 Python 工程師都踩過的坑。它的根源是搞混了兩個東西：**文字（`str`）** 與 **位元組（`bytes`）**。Python 3 把它們嚴格分開——這是 Py2→Py3 最重要的改變。這章講清楚字元編碼、`str` 與 `bytes` 的關係，以及如何不再被亂碼與編碼錯誤困擾。

## 💡 白話導讀（建議先讀）

`UnicodeDecodeError`——中文使用者八成踩過。根源是混淆了兩個東西，用電報來分：

- **`str` ＝ 訊息的內容**：「你好」這兩個**字**。人類世界的東西。
- **`bytes` ＝ 打出去的電報碼**：一串 0-255 的數字。機器世界的東西（存檔、網路傳的都是它）。

兩個世界怎麼轉換？需要一本「電碼本」——**編碼（encoding）**，最通用的一本叫 **UTF-8**：

```text
str ──.encode("utf-8")──> bytes    （發電報：文字 → 電碼）
bytes ──.decode("utf-8")──> str    （收電報：電碼 → 文字）
```

那 **Unicode** 是什麼？它是「全世界每個字元的**編號總表**」（`中` 是 4E2D 號）——只管編號，不管怎麼打成電報。編號表是 Unicode，打電報的規則才是 UTF-8。

`UnicodeDecodeError` 的真相通常就一句：**發報用 A 電碼本，收報卻拿 B 電碼本查**（如檔案是 UTF-8 存的，你用 Big5 讀）。

實務守則叫 **Unicode 三明治**：

> **進來時立刻 decode 成 str → 程式內部全程用 str → 出去時才 encode 成 bytes。**

轉換只發生在邊界（開檔、網路收發），中間層永遠不碰 bytes。加一條:開檔永遠寫明 `encoding="utf-8"`,別賭系統預設。

## Why（為什麼）

電腦底層只認識**位元組（bytes）**——一串 0 和 1。但人類要處理**文字**——`a`、`中`、`é`、`👍`。從「文字」到「位元組」需要一套規則，叫做**編碼（encoding）**：哪個字元對應哪串位元組。同一個字 `中`，用 UTF-8 編是 3 個位元組、用 Big5 編是 2 個位元組、用 UTF-16 編是 2 個位元組——**同一個字元，不同編碼產生不同的位元組**。

問題就出在這裡：如果你**用 A 編碼寫入、卻用 B 編碼讀取**，就得到亂碼或 `UnicodeDecodeError`。這是實務最常見的痛：讀一個檔案炸出 `UnicodeDecodeError`、API 回來的中文變亂碼、在 Windows 印個 emoji 就 `UnicodeEncodeError`。

Python 3 為了根治這類混亂，做了一個關鍵設計：**嚴格區分 `str`（文字，Unicode 字元序列）與 `bytes`（位元組序列）**，且**兩者不能混用**——要轉換必須**明確指定編碼**（`str.encode()` / `bytes.decode()`）。這比 Python 2「str 既是文字又是位元組、隱式轉換」的混亂安全得多，但也要求你**清楚意識到「我現在處理的是文字還是位元組」**。理解這個模型，`UnicodeDecodeError` 就不再神秘。這章講透它，並連結 [字串](04-strings.md)、[檔案 I/O](../11-stdlib/06-io.md)。

## Theory（理論：str vs bytes 與 Unicode）

先分清三個概念（電報模型的三個角色）：

- **字元集 / Unicode**：一張「字元 ↔ 編號（code point，碼位）」的巨大對照表——編號總表。`A` 是 U+0041、`中` 是 U+4E2D、`👍` 是 U+1F44D。Unicode 只定義編號，**不規定怎麼存成位元組**。
- **編碼（encoding）**：把碼位**轉成位元組**的規則——電碼本。UTF-8、UTF-16、Big5、Latin-1 都是。**UTF-8 是網路與檔案的事實標準**（相容 ASCII、變長、省空間）。
- **`str` vs `bytes`**：
  - **`str`**：Python 的**文字**型別——一串 Unicode 字元（碼位）。`"café"`、`"中文"`。與編碼無關（抽象的字）。
  - **`bytes`**：一串**位元組**（0–255）。`b"caf\xc3\xa9"`。是 str 經某編碼後的產物，或來自檔案/網路的原始資料。

**核心關係**：

```text
str  --.encode(編碼)-->  bytes      （發電報：文字 → 位元組）
bytes --.decode(編碼)-->  str        （收電報：位元組 → 文字）
```

**關鍵心法——Unicode 三明治**：

> 輸入時 decode 成 str → 內部全用 str → 輸出時 encode 成 bytes。

`str` 給人看、`bytes` 給機器存/傳；轉換只在**邊界**（讀寫檔案、網路收發）發生。

## Specification（規範：encode / decode）

**轉換**：

```python
text = "café"
data = text.encode("utf-8")     # str → bytes：b'caf\xc3\xa9'
back = data.decode("utf-8")     # bytes → str：'café'
```

- **`str.encode(encoding="utf-8", errors="strict")`**：文字轉位元組。
- **`bytes.decode(encoding="utf-8", errors="strict")`**：位元組轉文字。
- 兩者的 `encoding` 預設是 **UTF-8**（Python 3 的預設），但**明確指定**是好習慣。

**`errors` 參數**（遇到無法處理的字元/位元組時）：

- `"strict"`（預設）：拋 `UnicodeDecodeError`/`UnicodeEncodeError`。
- `"replace"`：用替換字元（`�` / `?`）代替。
- `"ignore"`：直接丟棄。
- `"backslashreplace"` / `"xmlcharrefreplace"`：轉成跳脫序列。

**bytes 字面值與操作**：

```python
b"hello"              # bytes 字面值（只能含 ASCII，非 ASCII 用 \xNN）
b"caf\xc3\xa9"        # 明確的位元組
bytes([99, 97, 102])  # 從整數列表
data.hex()            # 轉十六進位字串（除錯好用）
```

**檔案 I/O 的編碼**（見 [io](../11-stdlib/06-io.md)）：

```python
open("f.txt", "r", encoding="utf-8")   # 文字模式：自動 decode → str（務必指定 encoding）
open("f.bin", "rb")                     # 二進位模式：讀到 bytes（不 decode）
```

**永遠明確指定 `encoding`**——否則用平台預設（Windows 常是 cp950/cp1252，Linux 是 UTF-8），跨平台就會出事。

## Implementation（底層：UTF-8、為何 len 不同、Windows 主控台陷阱）

**UTF-8 為何是首選**：UTF-8 是**變長編碼**——ASCII 字元（`a`、`1`）用 **1 個位元組**（且與 ASCII 完全相容）、常見拉丁字元（`é`）用 2 個、中日韓文字用 3 個、emoji 用 4 個。好處：純英文文字不浪費空間、相容既有 ASCII、無位元組順序問題（不像 UTF-16 有 BOM/大小端）。所以網路傳輸、檔案儲存、原始碼幾乎都用 UTF-8。

**為何 `len(str)` 與 `len(bytes)` 不同**：`len(str)` 數的是**字元（碼位）數**、`len(bytes)` 數的是**位元組數**。`"café"` 有 4 個字元，但 UTF-8 編碼後是 5 個位元組（`é` 佔 2 個）。emoji `👍` 是 **1 個字元**，UTF-8 編碼是 **4 個位元組**。這解釋了一個常見困惑——「為什麼這個字串長度算起來不對」：你可能在數位元組數，或反之。處理文字長度看 `len(str)`（字元數），處理儲存/傳輸大小看 `len(bytes)`。

**`UnicodeDecodeError` 的真正成因**：當你 `bytes.decode(編碼)`，Python 依該編碼的規則解讀位元組。若這串位元組**不符合該編碼的規則**（如用 `ascii` 解一個含 `\xc3` 的 UTF-8 位元組——ASCII 只認 0–127），就拋 `UnicodeDecodeError`。**根因幾乎都是「用錯編碼」**：資料是 UTF-8 卻用 Big5/ASCII 解、或反之。修法是**用資料真正的編碼去 decode**（通常是 UTF-8）。

**Windows 主控台的 `UnicodeEncodeError` 陷阱**：在 Windows 上 `print("👍")` 或 `print("中文")` 可能拋 `UnicodeEncodeError: 'cp950' codec can't encode...`。原因：`print` 要把 `str` 編碼成主控台的編碼才能顯示，而 Windows 主控台預設是 **cp950（繁中）/cp1252**，不是 UTF-8——這些編碼無法表示 emoji 或某些字元。這**不是你的字串有問題**，是主控台編碼的限制。解法：設 `PYTHONUTF8=1` 或 `PYTHONIOENCODING=utf-8`、用支援 UTF-8 的終端、或把輸出寫進 UTF-8 檔案而非印到主控台。這也是為何下面的可執行範例刻意用 `hex()`、`ascii()` 等 **ASCII 安全** 的方式顯示——確保跨平台都能跑、輸出一致。

## Code Example（可執行的 Python 範例）

```python
# encoding_demo.py — str/bytes、編碼往返、UnicodeDecodeError（跨平台安全輸出）
from __future__ import annotations


def main() -> None:
    text = "café"  # str：4 個 Unicode 字元

    # str → bytes（encode）；bytes → str（decode）
    utf8 = text.encode("utf-8")
    print(f"字元數 len(str) = {len(text)}")
    print(f"utf-8 bytes = {utf8}，位元組數 = {len(utf8)}")
    print(f"往返一致 decode(utf-8) == text: {utf8.decode('utf-8') == text}")

    # 同一字串、不同編碼 → 不同位元組（用 hex 顯示，ASCII 安全）
    print(f"utf-8   hex: {text.encode('utf-8').hex()}")
    print(f"utf-16le hex: {text.encode('utf-16-le').hex()}")
    print(f"latin-1 hex: {text.encode('latin-1').hex()}")

    # 經典錯誤：用錯編碼 decode → UnicodeDecodeError
    try:
        utf8.decode("ascii")
    except UnicodeDecodeError as exc:
        print(f"用 ascii 解 utf-8 位元組 → {type(exc).__name__}")

    # errors 參數：replace / ignore（用 ascii() 安全顯示）
    print(f"errors=replace: {ascii(utf8.decode('ascii', errors='replace'))}")
    print(f"errors=ignore : {ascii(utf8.decode('ascii', errors='ignore'))}")

    # len 陷阱：字元數 vs 位元組數（emoji 佔 1 字元、4 位元組）
    thumb = "\U0001f44d"  # 👍
    print(
        f"emoji 字元數={len(thumb)} "
        f"utf-8位元組={len(thumb.encode('utf-8'))} "
        f"utf-16le位元組={len(thumb.encode('utf-16-le'))}"
    )


if __name__ == "__main__":
    main()
```

**預期輸出**：

```pycon
$ python encoding_demo.py
字元數 len(str) = 4
utf-8 bytes = b'caf\xc3\xa9'，位元組數 = 5
往返一致 decode(utf-8) == text: True
utf-8   hex: 636166c3a9
utf-16le hex: 630061006600e900
latin-1 hex: 636166e9
用 ascii 解 utf-8 位元組 → UnicodeDecodeError
errors=replace: 'caf��'
errors=ignore : 'caf'
emoji 字元數=1 utf-8位元組=4 utf-16le位元組=4
```

逐段解說：

- **encode/decode 往返**：`"café"`（4 字元）encode 成 UTF-8 是 `b'caf\xc3\xa9'`（5 位元組，`é` 佔 `\xc3\xa9` 兩個）；decode 回來與原字串**一致**。這是 Unicode 三明治的兩端。
- **同字串不同編碼**：`café` 在 UTF-8 是 `636166c3a9`、UTF-16LE 是 `630061006600e900`（每字元 2 位元組）、Latin-1 是 `636166e9`（`é` 剛好 1 位元組）——**同一文字，編碼不同、位元組全然不同**。這就是「用錯編碼解讀 = 亂碼」的根源。
- **`UnicodeDecodeError`**：用 `ascii` 解 UTF-8 的位元組——`\xc3`（195）超出 ASCII 的 0–127 → 拋 `UnicodeDecodeError`。**根因是用錯編碼**（該用 utf-8）。
- **`errors` 參數**：`replace` 把無法解的位元組換成 `�`（替換字元 `�`，此例兩個壞位元組 → 兩個）；`ignore` 直接丟棄成 `'caf'`。用於「寧可容錯也不要中斷」的場景，但會**遺失/破壞資料**，慎用。
- **len 陷阱**：emoji `👍` 是 **1 個字元**、UTF-8 佔 **4 個位元組**——`len(str)` 數字元、`len(bytes)` 數位元組，兩者常不同。
- **跨平台安全**：範例用 `hex()`、`ascii()` 顯示，避免在 Windows cp950 主控台印非 ASCII 字元導致 `UnicodeEncodeError`——這本身就是本章的實務教訓。

## Diagram（圖解：Unicode 三明治）

```mermaid
flowchart TD
    IN["輸入(bytes)<br/>檔案/網路/stdin"] -->|decode(編碼)| S1["str(文字)"]
    S1 --> CORE["程式內部<br/>全部用 str 處理文字"]
    CORE -->|encode(編碼)| OUT["輸出(bytes)<br/>檔案/網路/stdout"]
    NOTE["Unicode 三明治:<br/>邊界 decode/encode,<br/>內部只用 str"]
    U["Unicode: 字元↔碼位(抽象)<br/>編碼: 碼位↔位元組(UTF-8/16/Big5)"]
    style S1 fill:#e3f2fd
    style CORE fill:#e8f5e9
    style NOTE fill:#fff3e0
```

## Best Practice（最佳實踐）

- **內部一律用 `str` 處理文字，只在邊界 encode/decode**（Unicode 三明治）。
- **一切用 UTF-8**：檔案、API、原始碼——除非有明確理由。
- **開檔、收發一律明確指定 `encoding="utf-8"`**：別依賴平台預設（Windows cp950 會出事）。
- **清楚意識「我現在是 str 還是 bytes」**：處理網路/檔案原始資料是 bytes、處理文字是 str。
- **文字長度看 `len(str)`（字元）、儲存大小看 `len(bytes)`（位元組）**。
- **除錯編碼問題用 `.hex()` 看原始位元組**：一眼看出是什麼編碼。
- **Windows 印非 ASCII 出錯**：設 `PYTHONUTF8=1`、用 UTF-8 終端、或寫檔而非印主控台。
- **謹慎用 `errors="ignore"/"replace"`**：會遺失/破壞資料；優先修正編碼。

## Common Mistakes（常見誤解）

- **搞混 str 與 bytes**：把 bytes 當文字用、或反之（Py3 不能隱式轉換，會 `TypeError`）。
- **用錯編碼 decode**：資料是 UTF-8 卻用 Big5/ASCII 解 → `UnicodeDecodeError` 或亂碼。
- **開檔不指定 encoding**：吃平台預設，本機能跑、換機/上線就亂碼。
- **以為 `len` 是位元組數（或字元數）**：分清 `len(str)` 字元、`len(bytes)` 位元組。
- **用 `errors="ignore"` 掩蓋問題**：資料被默默破壞，之後更難查。
- **在 Windows 主控台 `print` emoji/中文炸 `UnicodeEncodeError`**：怪自己的字串，其實是主控台編碼限制。
- **以為「Unicode」是一種編碼**：Unicode 是字元集/碼位對照，UTF-8/16 才是編碼。
- **拼接 str 與 bytes**：`"a" + b"b"` → `TypeError`；先統一型別。

## Interview Notes（面試重點）

- **能清楚區分 `str`（Unicode 文字）與 `bytes`（位元組）**，以及 Python 3 嚴格分離、需明確 encode/decode（對比 Py2 的混亂）。
- **能解釋編碼是什麼**：碼位→位元組的規則，同字串不同編碼產生不同位元組；Unicode 是字元集不是編碼。
- **能講 `UnicodeDecodeError` 的成因與修法**：用錯編碼；用資料真正的編碼（通常 UTF-8）decode。
- **知道 Unicode 三明治**：邊界 decode/encode、內部只用 str。
- **知道 UTF-8 為何是首選**（變長、相容 ASCII、無 BOM/大小端問題）。
- **知道 `len(str)` vs `len(bytes)` 的差異**、開檔要指定 encoding、Windows 主控台編碼陷阱。

---

你已掌握 Python 的語言地基：動態型別與名稱綁定、數值與字串、流程控制、函式與參數、作用域與閉包、推導式與現代語法，以及字元編碼與 bytes/str。
下一章把這 16 章串成一張圖，並用「四大經典陷阱」驗收你的所得。

➡️ 下一章：[Part 2 統整：語言基礎全貌](17-summary.md)

[⬆️ 回 Part 2 索引](README.md)
