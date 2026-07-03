# 冪等性設計

> 網路會逾時、客戶端會重試、訊息會重複投遞——在分散式系統裡，**同一個操作被執行多次**幾乎無法避免。若「扣款」被執行兩次，使用者就被多扣一次錢。**冪等性（idempotency）** 讓「重複執行」變得安全：做一次和做多次結果相同。這章講冪等的原理與實作。

## Why（為什麼）

分散式系統的一個殘酷事實：**你無法確定一個操作「只被執行了一次」**。考慮一個付款請求：

1. 客戶端發出「扣款 100 元」的請求。
2. 伺服器收到、成功扣款、準備回應「成功」。
3. **但回應在網路上丟失了**（逾時）。
4. 客戶端沒收到回應，以為失敗 → **重試** → 伺服器又扣了一次 → **重複扣款**！

問題的核心：客戶端收到逾時，它**不知道**「是請求沒送到（該重試）」還是「請求成功了但回應丟了（不該重試）」。為了不漏掉，客戶端**傾向重試**——於是重複操作發生。這種情況無所不在：[至少一次投遞](04-message-queue.md)的訊息會重複、[熔斷/重試](../21-microservices/07-rate-limit-circuit-breaker.md)機制會重送、使用者連點兩下按鈕、負載平衡重送請求。

**冪等性（idempotency）** 是解法——設計操作使得「**執行一次和執行 N 次，結果相同**」。這樣重複執行就**無害**：付款重試不會多扣、訊息重複消費不會重複處理。冪等性是分散式系統可靠性的**基石**——因為你無法消除重複，只能讓重複安全。這章講清楚哪些操作天生冪等、如何讓非冪等操作變冪等（**idempotency key**）。它是 [訊息佇列](04-message-queue.md)、[重試](../21-microservices/07-rate-limit-circuit-breaker.md)、[分散式鎖](03-distributed-lock.md) 的共同配套。

## Theory（理論：冪等的定義與分類）

**冪等（idempotent）的定義**：一個操作執行一次和執行多次，對系統狀態的**影響相同**。數學上 `f(f(x)) = f(x)`。

**哪些操作天生冪等**：

- **讀取（GET）**：讀幾次都不改變狀態，天生冪等。
- **設定為絕對值**：`set balance = 100`（不管執行幾次，結果都是 100）——冪等。
- **刪除（DELETE）**：刪一個已刪除的東西，結果一樣（不存在）——冪等。
- **PUT（替換）**：用完整資料替換，多次結果相同——冪等。

**哪些天生不冪等（危險）**：

- **相對變化**：`balance = balance - 100`（扣款）——執行兩次扣兩次！**這是最危險的**。
- **POST（建立）**：每次建立一筆新資源——執行兩次建兩筆。
- **追加（append）**：每次加一筆——重複會多加。

**HTTP 方法的冪等性**（REST 設計原則）：GET、PUT、DELETE 應設計成冪等；POST 通常不冪等。

**讓非冪等操作變冪等的核心手法——idempotency key（冪等鍵）**：

客戶端為每個操作生成一個**唯一的冪等鍵**（如 UUID），隨請求送出。伺服器**記錄處理過的鍵**：

- 若這個鍵**沒見過** → 執行操作、記錄鍵（+結果）。
- 若這個鍵**見過** → **不重複執行**，直接回上次的結果。

這樣同一個操作（同一個 key）不管被送幾次，都只**實際執行一次**——把不冪等的操作（扣款）變成冪等的。

## Specification（規範：idempotency key）

**客戶端**：為每個「有副作用、不可重複」的操作生成唯一 key，重試時**用同一個 key**：

```text
POST /payments
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
{ "amount": 100 }
```

**伺服器**：

```python
def process_payment(idempotency_key, amount):
    # 檢查是否已處理過這個 key
    existing = store.get(idempotency_key)
    if existing is not None:
        return existing            # 已處理 → 回上次結果，不重複扣款

    result = do_charge(amount)     # 首次 → 執行
    store.set(idempotency_key, result)  # 記錄鍵與結果
    return result
```

**關鍵細節**：

- **「檢查 + 記錄」要原子**：否則兩個並發的相同請求可能都通過檢查、都執行（race）。用資料庫唯一約束（insert 唯一鍵，重複會失敗）或[分散式鎖](03-distributed-lock.md)保證原子。
- **記錄結果**：不只記「處理過」，還記結果——重複請求要回**一樣的**回應。
- **設過期**：冪等鍵記錄不必永久保存（設 TTL，如 24 小時），但要涵蓋合理的重試窗口。
- **鍵的範圍**：通常 per-操作類型 + per-使用者，避免不同操作撞鍵。

**其他冪等手法**：用**唯一業務鍵**（如訂單號）+ 資料庫唯一約束天然去重；用**條件更新**（樂觀鎖/版本號）；設計成**絕對值操作**而非相對變化。

## Implementation（底層：原子去重與 exactly-once 幻覺）

**冪等鍵的原子去重為何關鍵**：`process_payment` 的「檢查 key 是否存在 → 不存在則執行並記錄」如果**不是原子的**，就有 race condition：兩個攜帶**同一 key** 的並發請求（如客戶端同時重試兩次），可能**都**通過「檢查（key 不存在）」、**都**執行扣款——重複扣款又發生了，冪等失效。所以「檢查 + 記錄」必須原子。實務常用**資料庫唯一約束**：把 idempotency key 設為唯一索引，處理時**先 insert 這個 key**（成功才繼續執行、失敗代表已存在就回舊結果）——insert 的唯一性由資料庫原子保證，天然序列化了並發的相同請求。這比先查再寫可靠。

**冪等如何實現「效果上的 exactly-once」**：[前一章](04-message-queue.md)說純 exactly-once 投遞極難，實務用「**at-least-once 投遞 + 消費者冪等**」。原理是：投遞層保證「不丟」（可能重複），冪等層保證「重複無害」（同一操作只生效一次）——兩者疊加，**效果上**等同 exactly-once（每個操作恰好生效一次），即使訊息實際被投遞/處理了多次。這是分散式系統達成「恰好一次」語意的標準做法——不是靠完美的投遞，而是靠冪等消化重複。這也是為何冪等是分散式可靠性的基石。

**冪等 vs 分散式鎖**：兩者都處理「並發/重複」，但角度不同。[鎖](03-distributed-lock.md)是「**同一時刻只讓一個執行**」（互斥），冪等是「**執行多次也沒關係**」（重複安全）。冪等通常更**務實、更有韌性**——因為鎖本身在分散式下難做對（會過期、會有雙持有者），而冪等從根本上讓「即使重複也無害」，不依賴完美的互斥。很多場景用「合理的鎖 + 冪等兜底」比追求完美的鎖更可靠。下面範例實作 idempotency key 防重複扣款。

## Code Example（可執行的 Python 範例）

```python
# idempotency.py — idempotency key 防重複扣款（純標準庫，可執行）
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PaymentService:
    """用 idempotency key 讓「扣款」冪等：同一 key 重試不重複扣。"""

    balance: int = 1000
    # 記錄處理過的 idempotency key → 結果
    _processed: dict[str, dict[str, object]] = field(default_factory=dict)

    def charge(self, idempotency_key: str, amount: int) -> dict[str, object]:
        # 檢查是否已處理（實務用 DB 唯一約束原子化「檢查+記錄」）
        if idempotency_key in self._processed:
            return {**self._processed[idempotency_key], "replayed": True}

        # 首次：實際扣款
        if self.balance < amount:
            raise ValueError("餘額不足")
        self.balance -= amount
        result: dict[str, object] = {"charged": amount, "balance": self.balance}
        self._processed[idempotency_key] = result
        return {**result, "replayed": False}


def main() -> None:
    svc = PaymentService(balance=1000)
    key = "pay-abc-123"

    # 第一次扣款（首次執行）
    r1 = svc.charge(key, 100)
    print(f"第一次: {r1}")

    # 網路逾時 → 客戶端用「同一個 key」重試（不該重複扣！）
    r2 = svc.charge(key, 100)
    print(f"重試(同 key): {r2}  ← replayed=True，回上次結果，沒重複扣")

    r3 = svc.charge(key, 100)
    print(f"再重試(同 key): {r3}  ← 仍不重複扣")

    print(f"\n餘額 = {svc.balance}（只扣了一次 100，非三次）")

    # 不同的操作用不同 key → 正常各自扣款
    r4 = svc.charge("pay-def-456", 50)
    print(f"\n不同 key 的新扣款: {r4}")
    print(f"餘額 = {svc.balance}（1000 - 100 - 50 = 850）")


if __name__ == "__main__":
    main()
```

**預期輸出**：

```pycon
$ python idempotency.py
第一次: {'charged': 100, 'balance': 900, 'replayed': False}
重試(同 key): {'charged': 100, 'balance': 900, 'replayed': True}  ← replayed=True，回上次結果，沒重複扣
再重試(同 key): {'charged': 100, 'balance': 900, 'replayed': True}  ← 仍不重複扣

餘額 = 900（只扣了一次 100，非三次）

不同 key 的新扣款: {'charged': 50, 'balance': 850}
餘額 = 850（1000 - 100 - 50 = 850）
```

逐段解說：

- **`charge` + idempotency key**：先檢查這個 key 是否處理過。**沒見過** → 實際扣款、記錄 key+結果；**見過** → 直接回上次結果（`replayed=True`），**不重複扣**。
- **首次扣款**：key `pay-abc-123` 首次 → 扣 100，餘額 900，`replayed=False`。
- **同 key 重試不重複扣**：客戶端因逾時用**同一個 key** 重試兩次——兩次都回上次結果（餘額仍 900），**沒有重複扣款**。這就是冪等鍵的價值：把不冪等的「扣款」變成「重複執行也安全」。
- **餘額只扣一次**：三次 `charge`（同 key）後餘額仍 900——只實際扣了一次 100。若沒有冪等鍵，會扣三次變 700。
- **不同 key 各自生效**：新操作用新 key `pay-def-456` → 正常扣 50（餘額 850）。冪等鍵只去重「同一操作的重複」，不影響不同操作。
- **要點**：idempotency key + 原子的「檢查+記錄」，把不冪等操作變冪等，讓重試/重複投遞無害。這是分散式可靠性的基石。

## Diagram（圖解：idempotency key 去重）

```mermaid
flowchart TD
    REQ["請求(Idempotency-Key: K)"] --> CHECK{"K 處理過?"}
    CHECK -->|否(首次)| EXEC["執行操作(扣款)"]
    EXEC --> STORE["原子記錄 K + 結果"]
    STORE --> RESP["回結果"]
    CHECK -->|是(重複)| REPLAY["不執行,回上次結果"]
    REPLAY --> RESP
    NOTE["投遞層 at-least-once(不丟)<br/>+ 冪等層(重複無害)<br/>= 效果上 exactly-once"]
    style EXEC fill:#e8f5e9
    style REPLAY fill:#fff3e0
    style NOTE fill:#e3f2fd
```

## Best Practice（最佳實踐）

- **有副作用、不可重複的操作都要冪等**：付款、下單、發送——假設「一定會被重複執行」。
- **用 idempotency key 讓非冪等操作變冪等**：客戶端生成唯一 key、重試用同一個。
- **「檢查 + 記錄」要原子**：用 DB 唯一約束或[鎖](03-distributed-lock.md)，防並發重複執行。
- **記錄結果並回放**：重複請求回一樣的回應。
- **設計成絕對值/條件更新而非相對變化**：`set = X` 天生冪等，`= x - 100` 不是。
- **善用唯一業務鍵 + DB 唯一約束**天然去重（如訂單號）。
- **冪等鍵設合理 TTL**：涵蓋重試窗口即可，不必永久。
- **at-least-once + 冪等 達成效果上的 exactly-once**：可靠訊息處理的標準組合。

## Common Mistakes（常見誤解）

- **假設操作只執行一次**：分散式下重複無法避免，不設計冪等 → 重複扣款/重複下單。
- **「檢查 + 記錄」不原子**：並發的相同請求都通過檢查、都執行；用 DB 唯一約束。
- **相對變化操作不做冪等**：`balance -= 100` 重試就多扣。
- **只記「處理過」不記結果**：重複請求無法回一致的回應。
- **冪等鍵永久保存**：無限膨脹；設 TTL。
- **以為有[鎖](03-distributed-lock.md)就不用冪等**：鎖會過期/雙持有者，冪等更根本、更有韌性。
- **消費 at-least-once 訊息不冪等**：重複消費導致重複副作用。
- **冪等鍵範圍不當**：太大（全域）易誤撞、太小涵蓋不足。

## Interview Notes（面試重點）

- **能定義冪等**（執行一次與多次結果相同）並說明分散式為何無法避免重複（逾時後客戶端不知該不該重試）。
- **能分辨天生冪等（GET/PUT/DELETE/絕對值）vs 不冪等（POST/相對變化/append）** 的操作。
- **能講 idempotency key 的機制**：唯一鍵 + 原子的「檢查+記錄」+ 回放結果。
- **能解釋「at-least-once + 冪等 = 效果上 exactly-once」**——分散式達成恰好一次的標準做法。
- **知道「檢查+記錄」原子性的重要**（DB 唯一約束）。
- **能對比冪等與分散式鎖**：冪等（重複無害）通常比鎖（互斥）更務實有韌性。

---

➡️ 下一章：[Saga 與分散式交易](07-saga.md)

[⬆️ 回 Part 22 索引](README.md)
