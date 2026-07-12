# argparse 與命令列工具

> 手動解析 `sys.argv` 遲早出錯——`argparse` 幫你處理位置引數、選項、旗標、型別轉換、預設值、說明訊息、錯誤處理。它是標準庫做命令列工具的正解。

## 💡 白話導讀（建議先讀）

如果你只用過 `python script.py`,這章的名詞會像天書。別急,我們從**最前面**講起。

> **一句話先抓重點:`argparse` 是把「終端機那串生字」翻譯成「程式裡好用的變數」的翻譯官。**
> 沒有它,你得自己一個字一個字拆、自己轉型別、自己報錯;有了它,宣告一下要收什麼,剩下全包。下面從零慢慢拆。

### 第一步:什麼是「命令列參數」?

你在終端機打 `python script.py`,程式就跑起來。但你其實可以**在後面多打幾個字**:

```bash
python script.py photo.jpg --width 800 -v
```

跟在程式後面的 `photo.jpg`、`--width 800`、`-v`,就是**命令列參數（command-line arguments）**——你在「啟動程式的當下」順便交代給它的指示。

> 🧋 想像去飲料店點「**大杯珍奶**,半糖,去冰」:「珍奶」是**主角**(一定要點),「半糖、去冰」是**備註**(可加可不加)。命令列參數就是你下單(啟動程式)時附帶的這些交代。

### 第二步:Python 怎麼收到這些字?——`sys.argv`

Python 把它們**原封不動**塞進一個 list,叫 `sys.argv`:

```python
import sys
# 假設執行:python script.py photo.jpg --width 800
print(sys.argv)   # ['script.py', 'photo.jpg', '--width', '800']
```

注意兩件事:(1) **全部都是字串**——連 `800` 都是字串 `"800"`;(2) 它**只是一串沒整理過的字**,程式名也混在裡面。

### 第三步:自己整理這串字,很痛苦

你得自己一個個判斷:哪個字是檔名?`--width` 後面那個要**轉成數字**?使用者**打錯順序**怎麼辦?**忘了給檔名**要報什麼錯?想支援 `--help` 還得自己印說明……寫著寫著就是一坨 `if` 地獄,而且**每寫一個腳本就要重來一次**。

### 第四步:`argparse` 就是替你收拾這串字的「櫃檯」

你只要**宣告**「本櫃檯收哪些單子」,剩下的解析、轉型、檢查、說明頁,它全包:

```python
import argparse

parser = argparse.ArgumentParser(description="批次處理圖片")
parser.add_argument("input")                          # 主角:檔名（必填）
parser.add_argument("--width", type=int, default=800) # 備註:寬度（自動幫你轉成數字！）
parser.add_argument("-v", "--verbose", action="store_true")  # 開關:要不要「囉嗦模式」

args = parser.parse_args()
# 執行 python prog.py photo.jpg --width 1024 -v 之後:
args.input      # "photo.jpg"
args.width      # 1024   ← 已經是 int,不再是字串！
args.verbose    # True    ← 有打 -v 就是 True,沒打就是 False
```

宣告完,櫃檯自動送你:**解析、型別轉換、必填檢查、錯誤提示,還有一份免費又專業的 `--help` 說明頁**——使用者打 `prog -h` 就看得到怎麼用,你一行說明頁都不用寫。

### 兩種參數 = 點餐的「主餐」和「加購」

- **位置參數（`input`）＝ 主餐**:按**順序**給、通常**必填**,直接給值不用寫 `--`（像「請先出示證件」）。
- **選用參數（`--width`、`-v`）＝ 加購**:用 `--名字` 指定、**有預設值**、順序隨意（像「加珍珠」「去冰」,不加也能出餐）。

### 什麼時候用、什麼時候用不到

- **會用到**:腳本要在終端機被「帶參數」執行——尤其是**做成工具、給別人用**(包括三個月後的你)。
- **用不到**:純粹自己跑一次、不帶任何參數的小腳本,就別為它加 argparse,直接寫死或用 `input()` 問就好。

一句定位:**只要腳本會給第二個人用,就值得上 argparse**——它把「一串生字」變成「整理好、型別正確、還附說明書」的參數。

## 🎯 什麼時候會用到

只要「**同一支程式要跑很多次、每次餵不同設定**」,就是 argparse 的舞台:

- **自己寫的工具腳本(最常見)**:`python 批次改圖.py ./照片 --寬度 800`、備份、爬蟲——同一支腳本換不同輸入重複跑。
- **資料處理 / ML 訓練腳本**:`python train.py --epochs 50 --lr 0.001`——把超參數做成參數,不改程式碼就能跑不同實驗。
- **專案的維運 / 管理指令**:`python manage.py migrate --env prod`、種子資料、批次匯入。
- **排程與 CI 工作**:cron、GitHub Actions 裡呼叫的腳本,靠參數傳日期/環境/開關。
- **發佈給別人裝的 CLI 工具**:別人 `pip install` 後在終端機打的指令,背後常是 argparse(或更現代的 click / typer,見下方 Best Practice)。

**反過來,什麼時候用不到**:只跑一次、不帶參數、設定不會變的小腳本——直接寫死或用 `input()` 問就好,別為它加 argparse。

> 💡 其實你**天天在用別人寫的 argparse**:`pip install`、`git commit -m`、`docker run -p 8080:80`——這些工具解析你參數的方式,就是 argparse 這類東西在做的事。

## Why（為什麼）

寫命令列工具（CLI）少不了解析引數：`myprog --verbose input.txt --count 5`。手動拆 `sys.argv` 又累又易錯（順序、型別、缺漏、`--help`）。**`argparse`** 幫你做這一切——宣告你要哪些引數，它負責解析、轉型、驗證、產生 `--help` 說明、處理錯誤。這是把腳本變成專業 CLI 工具的關鍵，也是 [os/sys](01-os-sys.md) 提到「複雜命令列別手動解析」的正解。

## Theory（理論：宣告式解析）

`argparse` 用**宣告式**——你「宣告」要哪些引數（名稱、型別、是否必填、說明），櫃檯自動：

- 解析 `sys.argv`。
- 型別轉換（字串 → int/float）。
- 驗證（必填、選項合法值）。
- 產生 `--help`/`-h` 說明頁。
- 錯誤時印友善訊息並退出。

兩類引數：

- **位置引數（positional）**：依位置，通常必填（`myprog input.txt`）——出示證件。
- **選用引數（optional）**：`-`/`--` 前綴，可有預設值（`--count 5`、`-v`）——加購選項。

## Specification（規範：argparse 用法）

```python
import argparse

parser = argparse.ArgumentParser(description="程式說明")

# 位置引數（必填）
parser.add_argument("filename", help="輸入檔案")

# 選用引數
parser.add_argument("-c", "--count", type=int, default=1, help="次數")
parser.add_argument("-v", "--verbose", action="store_true", help="詳細模式")
parser.add_argument("--mode", choices=["fast", "slow"], default="fast")
parser.add_argument("--files", nargs="+", help="多個檔案")  # 一個以上
parser.add_argument("--required-opt", required=True)

# 解析
args = parser.parse_args()      # 從 sys.argv 解析
print(args.filename, args.count, args.verbose)   # 用屬性取值
```

## Implementation（位置/選用、型別、旗標、choices、子命令）

### 位置引數 vs 選用引數

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input")             # 位置：必填，依位置
parser.add_argument("--output", "-o")    # 選用：--output 或 -o

# myprog data.txt --output result.txt
args = parser.parse_args()
args.input      # 'data.txt'
args.output     # 'result.txt'
```

位置引數依順序、通常必填；選用引數用 `--name`（長）/`-n`（短），順序無所謂、可有預設。

### 型別轉換與預設值

`type=` 自動轉型、`default=` 設預設：

```python
parser.add_argument("--count", type=int, default=1)      # 字串 → int
parser.add_argument("--rate", type=float, default=0.5)   # 字串 → float
parser.add_argument("--path", type=Path)                 # 可用任何可呼叫轉換
```

`argparse` 自動把命令列的字串轉成指定型別（轉換失敗會報友善錯誤）。

### 旗標：`action="store_true"`

布林旗標（有就 True、沒有就 False）用 `action="store_true"`：

```python
parser.add_argument("-v", "--verbose", action="store_true")
# myprog -v      → args.verbose == True
# myprog         → args.verbose == False
```

不必傳值，出現就是 True——用於開關（詳細模式、乾跑等）。

### `choices`：限定合法值

```python
parser.add_argument("--mode", choices=["dev", "prod", "test"], default="dev")
# --mode invalid  → argparse 自動報錯：invalid choice
```

`choices` 限定合法值，非法值 argparse 自動拒絕並提示——比自己 if 檢查省事。

### `nargs`：多個值

```python
parser.add_argument("files", nargs="+")     # 一個以上（回 list）
parser.add_argument("--tags", nargs="*")    # 零個以上
parser.add_argument("--coords", nargs=2, type=float)  # 剛好兩個
```

### 子命令（subcommands）：像 git

複雜 CLI 有子命令（`git commit`、`git push`）——用 `add_subparsers`：

```python
import argparse

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command")

# git commit -m "..."
commit = subparsers.add_parser("commit")
commit.add_argument("-m", "--message", required=True)

# git push origin
push = subparsers.add_parser("push")
push.add_argument("remote")

args = parser.parse_args()
if args.command == "commit":
    ...
```

子命令讓一個 CLI 有多種操作，各自有引數——這是 git、docker、pip 等工具的結構。

### 自動的 `--help`

`argparse` 自動產生 `-h`/`--help`——列出所有引數、型別、預設、說明。你只需在 `add_argument` 提供 `help=`，使用者就有完整文件。這是 argparse 勝過手動解析的一大好處。

## Code Example（可執行的 Python 範例）

```python
# argparse_demo.py
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """建立參數解析器。"""
    parser = argparse.ArgumentParser(
        description="示範 argparse 的命令列工具",
    )
    parser.add_argument("input", help="輸入檔案名")
    parser.add_argument("-c", "--count", type=int, default=1, help="重複次數")
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細模式")
    parser.add_argument(
        "--mode",
        choices=["fast", "slow"],
        default="fast",
        help="執行模式",
    )
    return parser


def run(args: argparse.Namespace) -> str:
    """依解析後的引數執行。"""
    lines = []
    if args.verbose:
        lines.append(f"[verbose] 模式={args.mode}")
    for i in range(args.count):
        lines.append(f"處理 {args.input} (第 {i + 1} 次)")
    return "\n".join(lines)


def demo() -> None:
    parser = build_parser()

    # 模擬命令列引數（實際會從 sys.argv 讀）
    args = parser.parse_args(["data.txt", "-c", "3", "-v", "--mode", "slow"])
    print("解析結果:")
    print(f"  input={args.input}, count={args.count}, verbose={args.verbose}, mode={args.mode}")
    print("\n執行:")
    print(run(args))


if __name__ == "__main__":
    demo()
```

**預期輸出**：

```pycon
$ python argparse_demo.py
解析結果:
  input=data.txt, count=3, verbose=True, mode=slow

執行:
[verbose] 模式=slow
處理 data.txt (第 1 次)
處理 data.txt (第 2 次)
處理 data.txt (第 3 次)
```

## Diagram（圖解：argparse 流程）

```mermaid
flowchart LR
    A[宣告引數 add_argument] --> B[parse_args 解析 sys.argv]
    B --> C[型別轉換 + 驗證]
    C --> D{合法?}
    D -- 是 --> E[Namespace: args.xxx 取值]
    D -- 否 --> F[印友善錯誤 + 退出]
    B -.自動.-> G["--help 說明"]
    style E fill:#e8f5e9
```

## Best Practice（最佳實踐）

- **命令列工具用 `argparse`**，別手動解析 `sys.argv`（見 [os/sys](01-os-sys.md)）——它處理型別、驗證、說明、錯誤。
- **每個引數提供 `help=`**：自動產生的 `--help` 就是完整文件。
- **用 `type=` 轉型、`default=` 設預設、`choices=` 限值、`action="store_true"` 做旗標**。
- **複雜工具用子命令**（`add_subparsers`），像 git/docker 的結構。
- **把 `parse_args` 與業務邏輯分開**（如範例：`build_parser` / `run`），方便測試。
- **考慮更現代的 CLI 框架**：`click`、`typer`（基於型別註記）對複雜 CLI 更好用，但 argparse 是標準庫、無需安裝。

## Common Mistakes（常見誤解）

- **手動解析 `sys.argv` 做複雜 CLI**：易錯、缺說明；用 argparse。
- **忘了 `type=`**：所有引數預設是**字串**；要 int/float 要指定 `type=int`。
- **旗標用 `type=bool`**：`type=bool` 對 `--flag false` 也是 True（非空字串為真）；布林旗標用 `action="store_true"`。
- **不提供 `help=`**：`--help` 沒有說明，使用者不知怎麼用。
- **位置引數與選用引數混淆**：位置無 `-` 前綴、必填；選用有 `--`、可預設。
- **`choices` 該用卻自己 if 檢查**：argparse 的 choices 更省事且自動提示。

## Interview Notes（面試重點）

- 知道 **`argparse` 是標準庫做 CLI 的正解**，取代手動解析 `sys.argv`：處理型別轉換、驗證、`--help`、錯誤。
- 知道 **位置引數（必填、依位置）vs 選用引數（`--`、可預設）**。
- 知道常用：**`type=`（轉型）、`default=`、`choices=`（限值）、`action="store_true"`（布林旗標）、`nargs`（多值）、子命令（add_subparsers）**。
- **知道旗標用 `action="store_true"` 而非 `type=bool`**（後者陷阱）。
- 知道所有引數預設是字串（要 `type=`）、自動產生 `--help`。
- 知道現代替代（click/typer）但 argparse 是標準庫。

---

➡️ 下一章：[random / math / statistics](11-random-math-statistics.md)

[⬆️ 回 Part 11 索引](README.md)
