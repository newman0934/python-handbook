# Part 19 面試題:雲原生與部署

> 對應 [Part 19 雲原生](../chapters/19-cloud-native/README.md)。DevOps/後端核心——Docker、gunicorn worker、12-factor、K8s liveness/readiness、graceful shutdown、可觀測性。

---

## Q1. Docker 解決什麼?image、container、layer 差在哪?

**考點**:Docker([01-docker](../chapters/19-cloud-native/01-docker.md))

**答**:Docker 解決**環境一致性**(「在我機器上能跑」)、隔離、可攜、輕量。

- **image(映像)**:唯讀的範本(應用 + 依賴 + 環境)。
- **container(容器)**:image 的執行實例。
- **layer(層)**:image 由多個唯讀層疊成(每個 Dockerfile 指令一層),**可快取**。

容器 vs VM:容器**共享 host kernel**(輕量、秒級啟動),VM 各帶完整 OS。

**追問**:

- **層快取的順序原則?** → **依賴放前、原始碼放後**——原始碼常變,若放前面每次改碼都要重裝依賴;放後面則依賴層可重用快取。
- **縮小映像?** → slim 基底、`--no-cache-dir`、`.dockerignore`、多階段建置(Q2)。
- **安全?** → 非 root、別把密鑰進映像、釘版本;**exec form** 才收得到訊號(graceful shutdown,見 Q7)。

---

## Q2. 多階段建置(multi-stage build)做什麼?

**考點**:多階段建置([02-multistage-build](../chapters/19-cloud-native/02-multistage-build.md))

**答**:分離 **build-time 依賴**(編譯器、build 工具)和 **run-time 依賴**——多階段建置讓最終映像**只保留執行需要的**:

```dockerfile
FROM python:3.12 AS builder      # build 階段:裝編譯工具、build
RUN pip install --user -r requirements.txt

FROM python:3.12-slim            # final 階段:只複製成品
COPY --from=builder /root/.local /root/.local   # 只搬依賴,丟棄 builder 其餘
```

最終映像只由**最後階段**構成,前階段的編譯工具等被丟棄——**省數百 MB**(小、快拉取、少攻擊面)。

**追問**:用 venv 搬依賴 + 設 `PATH`;**執行期系統函式庫的坑**(`libpq5` vs `libpq-dev`,漏裝會 `ImportError`);兩階段基底要一致。

---

## Q3. Gunicorn 和 Uvicorn 為什麼常一起用?worker 數怎麼定?

**考點**:gunicorn/uvicorn([03-gunicorn-uvicorn](../chapters/19-cloud-native/03-gunicorn-uvicorn.md))

**答**:Gunicorn 是 **WSGI(同步)** 的 pre-fork 伺服器,Uvicorn 是 **ASGI(非同步)**。FastAPI 生產常用 **Gunicorn 管理 + Uvicorn workers**——**Gunicorn 的 process 管理**(多核、crash 隔離、優雅重載)+ **Uvicorn 的 async**。

**pre-fork worker 模型**:master 管理、多 worker 共用 socket、**繞過 GIL 吃多核**、crash 隔離。

**worker 數經驗公式**:

- **同步**:`2 × cpu + 1`(worker 阻塞時要有備援)。
- **非同步**:約 `cpu`(單 worker 已能高並發,不需那麼多)。

**追問**:async worker 數可較少(單 worker 事件迴圈已重疊 I/O);**阻塞/CPU 密集會卡死事件迴圈**;參數 timeout/graceful-timeout/max-requests;生產常「**一容器一 Gunicorn、水平擴縮交給 K8s**」。

---

## Q4. 12-factor 的核心精神?為什麼無狀態是水平擴展的前提?

**考點**:12-factor([04-12-factor](../chapters/19-cloud-native/04-12-factor.md))

**答**:核心精神(懂精神,不必背 12 條):**無狀態、設定外置、可拋棄、環境對等**。

**無狀態為何是水平擴展前提**:若應用把狀態(session、上傳檔)存在**自己記憶體/本機**,不同實例的狀態就不一致(請求被分到別的實例就丟失)。**無狀態 → 實例可互換 → 狀態外置到共享後端(Redis/DB)→ 隨意增減實例**。

**追問**:設定走**環境變數**(build 一次跑多處、對等、不洩漏密鑰);**log 寫 stdout 而非檔案**(容器可拋棄、平台統一收集);這些原則讓應用能被 K8s 編排、擴縮、零停機。

---

## Q5. CI 和 CD 差在哪?

**考點**:CI/CD([05-ci-cd](../chapters/19-cloud-native/05-ci-cd.md))

**答**:

- **CI(持續整合)**:每次 push/PR **自動測試 + 檢查**(ruff + mypy + pytest),擋壞碼進主線。
- **CD**:自動**建置 + 部署**(delivery = 隨時可部署;deployment = 自動部署到生產)。

一條 Python pipeline:CI(ruff → mypy → pytest,**fail fast** 快的先跑)→ CD(build image → push → 部署 K8s)。

**追問**:CI 在**乾淨環境從頭跑**(可信、根除「我機器上能跑」);**branch protection**(PR 需 CI 綠才能合併)保護主線;矩陣測試(多版本)、依賴快取、Secrets 注入。

---

## Q6.(必考)K8s 的 liveness 和 readiness probe 差在哪?

**考點**:Kubernetes([06-kubernetes](../chapters/19-cloud-native/06-kubernetes.md))

**答**:K8s 解決**容器編排**(自動重啟、擴縮、滾動更新零停機、自我修復)。核心物件:**Pod**(最小可拋棄單位)、**Deployment**(維持副本 + 滾動更新)、**Service**(穩定入口 + 負載平衡)、ConfigMap/Secret。

**liveness vs readiness(高頻)**:

- **liveness(存活探針)**:失敗 → **重啟容器**(應用死了/卡死)。
- **readiness(就緒探針)**:失敗 → **移出流量**(暫時不能服務,如還在暖機、外部依賴斷)。

**外部依賴(DB)該放 readiness**(不能服務時移出流量,但別 liveness 失敗導致重啟——重啟解決不了 DB 掛)。

**追問**:滾動更新零停機(逐步替換 + readiness 把關);宣告式模型(宣告期望狀態、K8s 持續 reconcile);resources requests/limits、不可變 tag(別用 `latest`)。

---

## Q7. SIGTERM 和 SIGKILL 差在哪?怎麼優雅關閉?

**考點**:graceful shutdown([07-graceful-shutdown](../chapters/19-cloud-native/07-graceful-shutdown.md))

**答**:

- **SIGTERM**:**可攔截**——應觸發優雅關閉。
- **SIGKILL**:**無法攔截**、強制終止(超時才用)。

**K8s 關閉流程**:移出負載平衡 → 送 **SIGTERM** → 應用排空 → 退出 →(超過寬限期才)**SIGKILL**。

**優雅關閉正確順序**:**停收新請求 → 排空 in-flight(處理完手上的)→ 關資源(DB/連線)→ 退出**。

**追問**:**exec form 才收得到 SIGTERM**(shell form 收不到,被 shell 攔了);負載平衡傳播延遲的競態(用 `preStop` sleep 解);寬限期(`terminationGracePeriodSeconds`)要 > 最長請求時間。

---

## Q8. 可觀測性三大支柱?四個黃金訊號?

**考點**:可觀測性([08-observability](../chapters/19-cloud-native/08-observability.md))

**答**:三支柱各司其職、互補:

- **logs**:發生了**什麼**(離散事件)。
- **metrics**:量的**趨勢**(可聚合的數字時序)。
- **traces**:跨服務的**路徑/瓶頸**(一個請求的完整足跡)。

**排查流程**:metrics 發現異常 → traces 定位哪個服務/環節 → logs 看細節。

**四個黃金訊號**:**延遲、流量、錯誤、飽和度**。

**追問**:**結構化日誌**(JSON)在雲原生是必須(機器可解析、可查詢聚合、多容器匯集);**correlation/trace id** 串起跨服務足跡;**OpenTelemetry** 是統一標準;monitoring(監控已知)vs observability(探索未知);**別把敏感資料寫進 log**。

---

⬅️ [Part 18](part18-performance.md) ｜ [索引](README.md) ｜ ➡️ [Part 20 安全與系統設計](part20-security-system-design.md)
