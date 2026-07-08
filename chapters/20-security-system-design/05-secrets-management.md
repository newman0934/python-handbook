# 密鑰管理

> 資料庫密碼、API 金鑰、JWT 簽章密鑰、加密金鑰——這些**密鑰（secrets）** 一旦外洩，攻擊者就能長驅直入。而最常見的外洩原因蠢得驚人：把密鑰 commit 進 Git。這章講密鑰管理的原則：密鑰該存哪、怎麼傳、怎麼輪替、怎麼避免不小心洩漏。

## 💡 白話導讀（建議先讀）

資料庫密碼、API 金鑰、JWT 簽章密鑰——這些是你家的**鑰匙**。鑰匙管理的常識:

- **別把鑰匙黏在大門上**＝密鑰寫死在程式碼裡。
- **別拍照上傳社群**＝密鑰 commit 進 git——**git 歷史是永久的**,
  就算下一個 commit 刪掉,翻歷史照樣撈得到。這是最常見的外洩途徑,
  GitHub 上每天都有掃描機器人在收割公開 repo 的金鑰。
- **放保險箱**＝環境變數是基本盤([12-factor](../19-cloud-native/04-12-factor.md)),
  更進一步是密鑰管理系統(Vault、AWS/GCP Secrets Manager):集中存放、
  按需發放、每次存取都留紀錄(稽核)。
- **定期換鎖**＝輪替(rotation):就算某把鑰匙外洩,壽命有限;
  真的洩了,第一動作永遠是**立即輪替**,不是先查怎麼洩的。

已經 commit 出去怎麼辦?這章給完整的事故 SOP:
輪替密鑰 → 清 git 歷史(`git filter-repo`) → 檢查存取紀錄。
預防面則有:`.gitignore` 好 `.env`、pre-commit 掃密鑰(detect-secrets、gitleaks)、
CI 裡再掃一層。原則一句話:**密鑰與程式碼永遠分離,而且假設遲早會外洩——
讓「外洩的代價」小,比幻想「永不外洩」實際。**

## Why（為什麼）

密鑰是通往系統的鑰匙。它們外洩的後果是災難性的：DB 密碼外洩 → 整個資料庫被讀走/刪除；API 金鑰外洩 → 帳單暴增或服務被濫用；JWT 密鑰外洩 → 攻擊者能[偽造任意 token](04-jwt.md) 冒充任何人；雲端憑證外洩 → 整個基礎設施淪陷。

而密鑰外洩的頭號原因，是**把密鑰寫死在程式碼、然後 commit 進版控**：

```python
DATABASE_PASSWORD = "SuperSecret123"   # 🔴 一 push 就永遠留在 Git 歷史
API_KEY = "sk-abc123..."
```

一旦 push 到 GitHub（尤其公開 repo），自動化爬蟲**幾分鐘內**就會掃到並利用。更糟的是，就算你事後刪掉那行、再 commit，**密鑰仍留在 Git 歷史裡**——`git log` 一翻就有。唯一補救是**立刻輪替（作廢舊密鑰）**。

密鑰管理就是系統化地處理「密鑰的儲存、傳遞、輪替、稽核」，讓密鑰：**不進版控、不進映像、不進 log、可輪替、最小暴露**。這章講這些原則與 Python 實務。它與 [設定管理](../16-architecture/11-config-management.md) 密切相關（密鑰是最敏感的一種設定），但更聚焦資安面。

## Theory（理論：密鑰的生命週期）

密鑰管理涵蓋密鑰的整個生命週期：

- **儲存（storage）**：密鑰存哪？由不安全到安全：寫死在程式（最糟）→ 設定檔（仍可能進版控）→ **環境變數**（12-factor 基本盤）→ **密鑰管理系統**（Vault、雲端 Secrets Manager，最佳）。
- **傳遞（distribution）**：密鑰怎麼到達應用？環境變數注入、掛載成檔案、應用啟動時向 secrets manager 拉取。
- **輪替（rotation）**：定期更換密鑰，縮短「一把密鑰的有效壽命」——就算某把外洩，影響時間有限。外洩事件發生時必須**立即輪替**。
- **稽核（audit）**：記錄誰在何時存取了哪個密鑰，異常存取可追蹤。
- **最小暴露（least exposure）**：每個服務只拿到它需要的密鑰、只在需要時、權限最小。

**核心原則**：**密鑰與程式碼分離**（同 [12-factor](../19-cloud-native/04-12-factor.md) 第 3 條）+ **縱深防禦**（即使某層失守，其他層仍保護密鑰）。

## Specification（規範：怎麼管密鑰）

**開發環境——`.env` 檔（絕不 commit）**：

```bash
# .env（列入 .gitignore！）
DATABASE_URL=postgres://user:pass@localhost/db
JWT_SECRET=dev-secret-key
```

```python
# 用 pydantic-settings / python-dotenv 載入（見 設定管理章）
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    model_config = {"env_file": ".env"}
```

**必做**：`.env` 加進 `.gitignore`；提供 `.env.example`（只列鍵、不含真值）進版控讓新人知道要設什麼。

**正式環境——不用 `.env`，用平台的密鑰機制**：

- **環境變數**：由部署平台（[K8s Secret](../19-cloud-native/06-kubernetes.md)、雲平台設定）注入。
- **Secrets Manager**：HashiCorp Vault、AWS Secrets Manager、GCP Secret Manager——集中管理、加密儲存、存取控制、自動輪替、稽核。應用啟動時以身分（IAM role）向它拉取。這是正式環境的最佳實踐。

**防止不小心印出密鑰——用包裝型別**：`pydantic.SecretStr` 或自訂 wrapper，讓密鑰在 `repr`/`str`/log 中顯示成 `**********`，只有明確呼叫 `.get_secret_value()` 才拿到真值。這防止密鑰因 `print(settings)`、例外堆疊、log 而意外洩漏。

**掃描與防護**：用 `git-secrets`、`detect-secrets`、`trufflehog`、GitHub secret scanning 在 commit 前/CI 中掃出誤入的密鑰（見 [供應鏈安全](06-supply-chain.md)）。

## Implementation（底層：為何環境變數/包裝型別有效）

**為何環境變數比設定檔安全**：環境變數存在**行程的記憶體環境**，不落地成檔案、不易被 commit（沒有實體檔案可加進 Git）、且是語言/平台中立的注入點。部署平台能安全地把密鑰注入行程環境，而應用只讀 `os.environ`，不知道也不在乎密鑰從哪來——這種解耦讓密鑰能由平台的安全機制管理。相對地，設定檔是實體檔案，很容易不小心 `git add` 進去。

**為何 Secrets Manager 更進一步**：環境變數雖不進版控，但仍是「靜態」的——密鑰值固定、注入後就在那。Secrets Manager 提供：**加密儲存**（靜態加密）、**細緻存取控制**（哪個服務能拿哪個密鑰）、**動態密鑰**（如按需生成短效的 DB 憑證）、**自動輪替**、**完整稽核**。應用以自己的身分（雲 IAM）拉取，密鑰甚至不必長駐環境變數。這是縱深防禦的體現。

**包裝型別如何防洩漏**：像 `SecretStr` 這種型別，覆寫 `__repr__`/`__str__` 讓它們回傳遮罩字串（`'**********'`），真值只存在內部、需明確方法取出。為何有效？因為密鑰洩漏常是**間接**的——你沒有故意印密鑰，但 `logger.info(f"config={settings}")`、未捕捉例外的堆疊追蹤、debug 輸出，會把物件的 `repr` 印出來，密鑰就跟著跑進 log。用包裝型別，這些「順手印出」的路徑都只會顯示遮罩，真值不外流。下面範例實作一個這樣的 wrapper。

## Code Example（可執行的 Python 範例）

```python
# secrets_demo.py — 防洩漏的密鑰包裝型別 + 從環境載入（純標準庫，可執行）
from __future__ import annotations

import os


class SecretStr:
    """包裝密鑰：repr/str 遮罩，只有 get_secret_value() 取得真值。
    防止密鑰因 print/log/例外堆疊意外洩漏。"""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def get_secret_value(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "SecretStr('**********')" if self._value else "SecretStr('')"

    __str__ = __repr__


def mask(secret: str, visible: int = 4) -> str:
    """遮罩顯示：只露前幾碼（用於 log 稽核而不洩漏全部）。"""
    if len(secret) <= visible:
        return "*" * len(secret)
    return secret[:visible] + "*" * (len(secret) - visible)


def load_secret(name: str) -> SecretStr:
    """從環境變數載入密鑰（正式環境由平台注入，絕不寫死在程式）。"""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"缺少必要密鑰 {name}")
    return SecretStr(value)


def main() -> None:
    # 模擬平台注入的密鑰（實際由 K8s Secret / Secrets Manager 注入）
    os.environ["JWT_SECRET"] = "super-secret-signing-key-123"

    secret = load_secret("JWT_SECRET")

    # 意外印出物件 → 只看到遮罩（不洩漏真值）
    print(f"直接印出: {secret}")
    print(f"放進 log: config={{'jwt_secret': {secret!r}}}")

    # 只有明確取值才拿到真值（用於實際簽章等）
    print(f"實際使用(取真值長度): {len(secret.get_secret_value())} 字元")

    # 稽核用遮罩顯示（露前 4 碼確認是哪把，不洩漏全部）
    print(f"稽核顯示: {mask(secret.get_secret_value())}")


if __name__ == "__main__":
    main()
```

**預期輸出**：

```pycon
$ python secrets_demo.py
直接印出: SecretStr('**********')
放進 log: config={'jwt_secret': SecretStr('**********')}
實際使用(取真值長度): 27 字元
稽核顯示: supe***********************
```

逐段解說：

- **`SecretStr`**：覆寫 `__repr__`/`__str__` 回傳遮罩——這樣不論是 `print(secret)`、f-string、還是 log 裡順手印出物件，都只顯示 `**********`，**真值不會意外洩漏**。真值只有呼叫 `.get_secret_value()` 才拿得到（用於實際簽章/連線）。
- **「放進 log」**：模擬常見的洩漏路徑——把 config 物件印進 log。用了 SecretStr，log 裡只有遮罩，真值安全。
- **`load_secret`**：從環境變數載入（缺就啟動失敗，fail closed），**絕不寫死在程式**。正式環境由 K8s Secret / Secrets Manager 注入。
- **`mask`**：稽核時只露前 4 碼（`supe***...`），足以辨識「是哪一把密鑰」卻不洩漏全部——用於 log/監控。
- **要點**：密鑰從環境載入（不進程式碼）、用包裝型別防意外印出、稽核用遮罩——三層防止洩漏。`pydantic.SecretStr` 就是這個概念的成熟實作。

## Diagram（圖解：密鑰的流動）

```mermaid
flowchart TD
    subgraph STORE["密鑰儲存(依安全度)"]
        S1["🔴 寫死在程式(最糟)"]
        S2["⚠️ .env(開發用,不進版控)"]
        S3["✅ 環境變數(平台注入)"]
        S4["✅✅ Secrets Manager<br/>(加密/存取控制/輪替/稽核)"]
    end
    S3 -.注入.-> APP["應用行程"]
    S4 -.啟動時拉取.-> APP
    APP --> W["用 SecretStr 包裝<br/>(防 print/log/例外洩漏)"]
    W --> USE["get_secret_value()<br/>僅實際使用時取真值"]
    style S1 fill:#ffebee
    style S4 fill:#e8f5e9
    style W fill:#fff3e0
```

## Best Practice（最佳實踐）

- **密鑰絕不寫死在程式、絕不 commit 進版控**：`.env` 列入 `.gitignore`，提供 `.env.example`。
- **正式環境用平台密鑰機制**（K8s Secret / Secrets Manager），不用 `.env`。
- **用 `SecretStr` 類包裝密鑰**：防止 print/log/例外堆疊意外洩漏。
- **定期輪替 + 外洩時立即輪替**：縮短單把密鑰的暴露窗口。
- **最小權限**：每個服務只拿必要的密鑰、權限最小。
- **CI/pre-commit 掃描密鑰**（detect-secrets/trufflehog）：攔截誤入版控的密鑰。
- **密鑰不進 log、不進錯誤回應、不進映像**（見 [Docker](../19-cloud-native/01-docker.md)）。
- **一旦密鑰可能外洩，當作已外洩處理——立刻輪替**，別心存僥倖。
- **走 HTTPS 傳輸**，密鑰別放 URL query（會進 log）。

## Common Mistakes（常見誤解）

- **把密鑰寫死並 commit**：頭號外洩原因；爬蟲幾分鐘掃到。
- **以為刪掉那行 commit 就沒事**：密鑰仍在 Git 歷史裡；必須輪替。
- **密鑰進 log / 例外堆疊 / debug 輸出**：間接洩漏；用包裝型別遮罩。
- **正式環境也用 `.env` 檔**：檔案易被掛載錯、備份洩漏；用平台機制。
- **密鑰放 URL query string**：會被記進 access log、瀏覽器歷史、referer。
- **從不輪替**：一把密鑰用好幾年，外洩窗口無限大。
- **所有服務共用一把萬能密鑰**：一洩全洩；分而治之、最小權限。
- **把密鑰烤進 Docker 映像**：映像分層可被抽出；執行期注入。

## Interview Notes（面試重點）

- **能說出密鑰外洩的頭號原因（寫死+commit）與後果**，以及「刪了那行仍在 Git 歷史、必須輪替」。
- **能列密鑰儲存的安全梯度**：寫死 < 設定檔 < 環境變數 < Secrets Manager，並說明各自差異。
- **能解釋 Secrets Manager 的優勢**（加密儲存、存取控制、動態密鑰、輪替、稽核）。
- **知道用 `SecretStr` 包裝防止 print/log 意外洩漏**的原理。
- **知道輪替（定期 + 外洩時立即）、最小權限、CI 掃描** 等實務。
- **知道密鑰不進版控/映像/log/URL**，以及開發用 `.env`、正式用平台機制。

---

➡️ 下一章：[供應鏈安全](06-supply-chain.md)

[⬆️ 回 Part 20 索引](README.md)
