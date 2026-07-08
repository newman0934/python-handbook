# service discovery 服務發現

> 微服務環境裡，服務實例**不斷變動**——擴縮容、部署、故障重啟，IP 隨時在變。訂單服務要呼叫庫存服務，它怎麼知道庫存服務**現在**跑在哪些 IP？**服務發現（service discovery）** 就是回答這個問題的機制。這章講服務註冊、發現與負載平衡。

## 💡 白話導讀（建議先讀）

美食街的攤位**常搬家**:擴縮容、部署、故障重啟,服務實例的 IP 隨時在變。
訂單服務要找庫存服務,總不能把「攤位在 B2 第三格」寫死在程式裡——
明天它就搬去 B3 了。

解法是商場的**服務台樓層指南**——**服務註冊中心（service registry）**:
攤位開張來登記（服務啟動時註冊）、定期回報「我還在」（健康檢查）、
倒了除名（故障移除）。Consul、etcd、Eureka 都是這個角色。

拿到指南後,怎麼走過去?兩種模式:

- **客戶端發現＝自己去服務台問**:呼叫方直接查註冊中心拿實例清單,
  **自己挑一個**（自帶負載平衡）。省一跳,但每個服務都要內建「問路」邏輯。
- **伺服器端發現＝打總機轉接**:呼叫方只打一個**固定號碼**（如 K8s 的 Service 名）,
  轉接的事交給基礎設施。呼叫方超簡單——這就是為什麼
  [K8s 章](../19-cloud-native/06-kubernetes.md)說「其他服務一律打總機（Service）,
  別記攤位地址（Pod IP）」。

好消息:**如果你跑在 K8s 上,服務發現內建就有**——
`http://inventory-service` 這個 DNS 名就是總機。
這章講原理、兩種模式的取捨、以及不在 K8s 時怎麼用 Consul 自建
（含 Python 註冊與查詢的實作)。

## Why（為什麼）

在傳統的固定部署，服務位址是寫死的——庫存服務永遠在 `10.0.0.5:8080`。但在雲原生的微服務環境，這行不通：

- **實例動態變化**：自動擴縮容讓實例數隨流量增減、[K8s](../19-cloud-native/06-kubernetes.md) 隨時把 Pod 排到不同節點（新 IP）、故障的實例被替換成新的。
- **一個服務有多個實例**：庫存服務可能同時跑 5 個實例做負載平衡，且這 5 個的 IP 一直在變。

如果訂單服務把庫存服務的 IP 寫死，一擴縮/重啟就找不到人。**服務發現**解決這點：

- **服務註冊（registration）**：每個服務實例啟動時，把「我是庫存服務、在這個 IP:port」**登記**到一個**服務註冊中心（service registry）**；下線/故障時移除。
- **服務發現（discovery）**：呼叫方問註冊中心「庫存服務現在有哪些健康實例」，拿到當前的位址清單，再挑一個呼叫（負載平衡）。

於是服務間用**邏輯名稱**（"inventory-service"）互相尋找，而非寫死 IP——實例怎麼變動都能找到當前健康的對象。這是微服務動態環境的必要基礎設施。它與[健康檢查](06-health-checks.md)、[負載平衡](05-api-gateway.md)、[K8s Service](../19-cloud-native/06-kubernetes.md) 密切相關。

## Theory（理論：兩種發現模式）

**服務註冊中心（service registry）** 是核心——一個記錄「哪個服務有哪些健康實例在哪」的資料庫，如 **Consul、etcd、ZooKeeper、Eureka**（K8s 內建了服務發現）。實例註冊進來、健康檢查維持其存活狀態、下線時移除。

**兩種發現模式**：

- **客戶端發現（client-side discovery）**：呼叫方**直接問註冊中心**拿到實例清單，**自己**做負載平衡挑一個呼叫。呼叫方需要整合發現邏輯。（如 Netflix Eureka + Ribbon。）
- **伺服器端發現（server-side discovery）**：呼叫方只呼叫一個**固定的負載平衡器/gateway**，由它去問註冊中心、選實例、轉發。呼叫方無需知道發現細節。（如 [K8s Service](../19-cloud-native/06-kubernetes.md)——你呼叫 service 名，kube-proxy 幫你路由到某個 Pod。）

**健康檢查是關鍵配套**：註冊中心不能只記「有註冊過」，還要知道「**現在還健康嗎**」。透過**心跳（heartbeat）**（實例定期回報「我還活著」）或註冊中心**主動探測**（打實例的[健康端點](06-health-checks.md)）——**只把健康的實例回給呼叫方**，故障的自動剔除。這樣呼叫方永遠拿到能用的位址。

**負載平衡**：發現到多個健康實例後，用某種策略挑一個——round-robin（輪流）、random（隨機）、least-connections（最少連線）、weighted（加權）。

## Specification（規範：註冊中心的操作）

**核心操作**：

```text
register(service, instance)     # 實例啟動時登記
deregister(service, instance)   # 實例下線時移除
heartbeat(service, instance)    # 定期回報存活（否則 TTL 過期被剔除）
discover(service) → [healthy instances]  # 呼叫方查詢健康實例
```

**TTL / 心跳機制**：註冊時帶一個 **TTL（存活時間）**，實例要定期 `heartbeat` 續期；若某實例**沒在 TTL 內續期**（可能掛了/網路斷了），註冊中心自動剔除它——這保證清單裡都是「近期還活著」的。

**K8s 的服務發現**（最常見）：你不用自己架註冊中心——K8s 內建：

- 建一個 `Service`（邏輯名，如 `inventory-service`），它自動追蹤符合條件的健康 Pod（透過 [readiness probe](06-health-checks.md)）。
- 其他服務用 **DNS 名**（`inventory-service`）呼叫，K8s 自動負載平衡到某個健康 Pod。
- Pod 擴縮/替換時，Service 自動更新後端清單。

這是伺服器端發現的典型——應用只管用服務名呼叫，K8s 處理發現與負載平衡。

## Implementation（底層：TTL 剔除與健康過濾）

**為何需要 TTL / 心跳**：一個實例可能「不告而別」——程式崩潰、機器斷電、網路分區，來不及呼叫 `deregister`。如果註冊中心只在明確 deregister 時才移除，這些「死了但沒說」的實例會**留在清單裡**，呼叫方選到它們 → 呼叫失敗。**TTL + 心跳** 解決這點：實例要定期證明自己還活著（續期），註冊中心定期清掉「太久沒續期」的——這樣即使實例暴斃，它也會在 TTL 過期後自動被剔除。這是「最終會反映真實狀態」的自我修復機制，呼應 [K8s 控制迴圈](../19-cloud-native/06-kubernetes.md)。

**健康過濾為何重要**：`discover` 必須**只回健康實例**。一個實例可能還「註冊著」（TTL 沒過），但當下不健康（[readiness](06-health-checks.md) 失敗，如它的 DB 斷了）——這種實例不該收到流量。所以註冊中心結合健康檢查，把「註冊中且健康」的才回給呼叫方。這和 K8s 的 readiness probe 決定「Pod 是否在 Service 的後端清單裡」是同一個道理。

**發現 + 負載平衡的整體流程**：呼叫方要呼叫「庫存服務」時：(1) 向註冊中心 `discover("inventory")` 得到當前健康實例清單 `[10.0.1.3, 10.0.1.7, 10.0.2.1]`；(2) 用負載平衡策略（如 round-robin）挑一個；(3) 呼叫它。下次呼叫時清單可能已變（某實例擴出/剔除），但呼叫方每次都拿到最新的——**位址動態變化被透明化**。下面範例實作這個註冊中心 + 健康過濾 + round-robin。

## Code Example（可執行的 Python 範例）

```python
# service_discovery.py — 服務註冊中心 + 健康過濾 + round-robin（純標準庫，可執行）
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Instance:
    address: str
    healthy: bool = True
    last_heartbeat: float = 0.0


@dataclass
class ServiceRegistry:
    """服務註冊中心：註冊/剔除/心跳/發現健康實例。"""

    _services: dict[str, dict[str, Instance]] = field(default_factory=dict)
    ttl: float = 10.0

    def register(self, service: str, address: str, now: float) -> None:
        self._services.setdefault(service, {})[address] = Instance(address, True, now)

    def deregister(self, service: str, address: str) -> None:
        self._services.get(service, {}).pop(address, None)

    def heartbeat(self, service: str, address: str, now: float) -> None:
        inst = self._services.get(service, {}).get(address)
        if inst:
            inst.last_heartbeat = now

    def set_health(self, service: str, address: str, healthy: bool) -> None:
        inst = self._services.get(service, {}).get(address)
        if inst:
            inst.healthy = healthy

    def discover(self, service: str, now: float) -> list[str]:
        """只回「健康 + TTL 內有心跳」的實例（過濾掉暴斃/不健康的）。"""
        instances = self._services.get(service, {})
        return sorted(
            addr
            for addr, inst in instances.items()
            if inst.healthy and (now - inst.last_heartbeat) <= self.ttl
        )


class RoundRobinBalancer:
    def __init__(self) -> None:
        self._counter = 0

    def pick(self, instances: list[str]) -> str | None:
        if not instances:
            return None
        choice = instances[self._counter % len(instances)]
        self._counter += 1
        return choice


def main() -> None:
    registry = ServiceRegistry(ttl=10.0)
    # 三個庫存服務實例啟動註冊
    for addr in ("10.0.1.3", "10.0.1.7", "10.0.2.1"):
        registry.register("inventory", addr, now=0.0)

    print(f"發現健康實例: {registry.discover('inventory', now=1.0)}")

    # round-robin 負載平衡
    lb = RoundRobinBalancer()
    picks = [lb.pick(registry.discover("inventory", now=1.0)) for _ in range(4)]
    print(f"round-robin 挑選: {picks}")

    # 一個實例不健康 → 從發現結果剔除
    registry.set_health("inventory", "10.0.1.7", healthy=False)
    print(f"一實例不健康後: {registry.discover('inventory', now=1.0)}")

    # 一個實例暴斃（TTL 內沒心跳）→ 自動剔除
    print(f"20 秒後(超過 TTL 沒心跳): {registry.discover('inventory', now=20.0)}")


if __name__ == "__main__":
    main()
```

**預期輸出**：

```pycon
$ python service_discovery.py
發現健康實例: ['10.0.1.3', '10.0.1.7', '10.0.2.1']
round-robin 挑選: ['10.0.1.3', '10.0.1.7', '10.0.2.1', '10.0.1.3']
一實例不健康後: ['10.0.1.3', '10.0.2.1']
20 秒後(超過 TTL 沒心跳): []
```

逐段解說：

- **`register`**：三個庫存實例啟動時登記到註冊中心。
- **`discover`**：回傳當前**健康且 TTL 內有心跳**的實例清單——呼叫方拿到這個清單去呼叫。
- **round-robin**：`RoundRobinBalancer` 輪流挑實例（3 個實例、4 次挑選 → 第 4 次回到第 1 個），分散流量。
- **健康過濾**：`10.0.1.7` 標記不健康後，`discover` 不再回它——流量自動避開故障實例。
- **TTL 剔除**：到 `now=20.0`（超過 TTL=10、且沒續期心跳），所有實例都被視為暴斃剔除——回空清單。真實系統中實例會定期 `heartbeat` 續期，只有真的掛掉的才會 TTL 過期被剔除。
- **要點**：註冊中心 + 健康過濾 + TTL 心跳 + 負載平衡 = 呼叫方永遠拿到當前健康實例，位址動態變化被透明化。K8s Service 內建了這一整套。

## Diagram（圖解：服務發現流程）

```mermaid
flowchart TD
    subgraph REG["服務實例"]
        I1["庫存實例 A"] -->|register + heartbeat| R["服務註冊中心<br/>(Consul/etcd/K8s)"]
        I2["庫存實例 B"] -->|register + heartbeat| R
        I3["庫存實例 C(掛了)"] -.TTL 過期剔除.-> R
    end
    CALLER["訂單服務(呼叫方)"] -->|discover('inventory')| R
    R -->|回健康實例清單| CALLER
    CALLER -->|負載平衡挑一個| LB["round-robin/random"]
    LB -->|呼叫| I1
    style R fill:#e3f2fd
    style I3 fill:#ffebee
```

## Best Practice（最佳實踐）

- **用服務發現而非寫死 IP**：適應動態的實例變化。
- **結合健康檢查**（見 [健康檢查](06-health-checks.md)）：只把健康實例回給呼叫方。
- **用 TTL + 心跳自動剔除暴斃實例**：清單反映真實存活狀態。
- **K8s 環境直接用內建 Service 發現**：用服務名呼叫，別自架註冊中心。
- **選合適的負載平衡策略**：round-robin/least-connections/加權依場景。
- **呼叫方快取發現結果並定期刷新**：減少對註冊中心的查詢，但別快取太久（實例會變）。
- **搭配[熔斷/重試](07-rate-limit-circuit-breaker.md)**：發現到的實例仍可能呼叫失敗。
- **註冊中心本身要高可用**（多節點）：它是關鍵基礎設施，掛了全體找不到人。

## Common Mistakes（常見誤解）

- **寫死服務 IP**：擴縮/重啟後找不到人。
- **只註冊不做健康檢查**：把流量導向已故障的實例。
- **沒有 TTL/心跳**：暴斃的實例留在清單，呼叫失敗。
- **註冊中心單點**：它掛了全體服務互相找不到，系統癱瘓。
- **呼叫方不刷新發現結果**：快取過久，用到已剔除的舊實例。
- **在 K8s 裡還自架註冊中心**：重造輪子；用內建 Service。
- **發現後不處理呼叫失敗**：拿到健康清單不代表呼叫必成功；要重試/熔斷。
- **負載平衡策略不當**：如對有狀態服務用純隨機導致熱點。

## Interview Notes（面試重點）

- **能說明服務發現解決什麼**：動態環境中實例 IP 不斷變，用邏輯名找當前健康實例。
- **能區分客戶端發現 vs 伺服器端發現**（呼叫方自己選 vs 經負載平衡器/gateway），並知道 K8s Service 屬後者。
- **能解釋註冊中心 + 健康檢查 + TTL/心跳** 如何維持「健康實例清單」。
- **知道健康過濾與 TTL 剔除的必要性**（暴斃實例的處理）。
- **知道常見註冊中心**（Consul/etcd/ZooKeeper/Eureka）與 K8s 內建發現。
- **能連結負載平衡策略、熔斷/重試、註冊中心高可用**。

---

➡️ 下一章：[API gateway](05-api-gateway.md)

[⬆️ 回 Part 21 索引](README.md)
