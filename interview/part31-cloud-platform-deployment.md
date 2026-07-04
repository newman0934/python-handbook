# Part 31 面試題:雲端平台部署(AWS + GCP)

> 對應 [Part 31 雲端平台部署](../chapters/31-cloud-platform-deployment/README.md)。**雲端部署收尾**——AWS↔GCP 對照、IAM、容器/K8s/serverless 選型、託管 DB/儲存、密鑰/網路、Terraform、OIDC 免金鑰 CI/CD、可觀測性/成本、端到端上雲。

---

## Q1. 雲端部署模型有哪些?一個無狀態 Python API 該選哪種?

**考點**:部署模型光譜([01-cloud-overview](../chapters/31-cloud-platform-deployment/01-cloud-overview.md))

**答**:一條**抽象光譜**,越往右你管的越少:**IaaS(虛擬機,EC2/Compute Engine)→ CaaS(無伺服器容器,Fargate/Cloud Run)→ 託管 K8s(EKS/GKE)→ FaaS(函式,Lambda/Cloud Functions)**。越右維運越輕、控制越少。

**無狀態 HTTP 服務(如 FastAPI)首選容器(Fargate / Cloud Run)**——最少維運換到自動擴縮、按用量計費,又沒有 FaaS 的執行時間上限/冷啟動限制。

**追問**:AWS↔GCP 對照(EC2/Compute Engine、Fargate/Cloud Run、EKS/GKE、Lambda/Cloud Functions、RDS/Cloud SQL、S3/GCS);通用服務(容器/標準 DB)可攜 vs 專屬服務(DynamoDB/BigQuery)綁定;先垂直、先單雲,別一開始就多雲。

---

## Q2.(必考)IAM 的授權怎麼判斷?什麼是最小權限?為什麼用臨時憑證?

**考點**:IAM([02-iam](../chapters/31-cloud-platform-deployment/02-iam.md))

**答**:IAM =(principal 誰、action 做什麼、resource 對哪個)→ allow/deny。核心規則:**預設拒絕(default deny)+ 明確 deny 優先 + 需至少一個明確 allow**。

**最小權限(least privilege)**:只給完成任務所需的最小權限——限制被盜憑證/被注入程式的損害範圍,是資安底線。

**用臨時憑證而非長期金鑰**:應用/CI 掛 **role(AWS)/service account(GCP)** 取得**短命 + 自動輪替**的臨時憑證;長期 access key 一旦外洩就長期有效、常被寫死忘記,是頭號外洩來源。

**追問**:AWS policy 附到身分 vs GCP role 綁到資源;公開 S3 bucket、over-privileged role、寫死金鑰是經典事故;一個工作負載一個身分。

---

## Q3. Fargate/Cloud Run vs EKS/GKE 怎麼選?無狀態為什麼是硬需求?

**考點**:容器與 K8s([03-containers](../chapters/31-cloud-platform-deployment/03-containers-ecs-cloudrun.md) / [04-managed-k8s](../chapters/31-cloud-platform-deployment/04-managed-k8s.md))

**答**:**簡單無狀態服務 → 無伺服器容器(Fargate/Cloud Run)**:build→push registry→deploy,平台管擴縮/健康檢查/滾動更新;**複雜多服務編排、需 K8s 生態 → 託管 K8s(EKS/GKE)**,但複雜度與維運重得多,「能用 Cloud Run 就別上 K8s」。

**無狀態是硬需求**:實例隨時被建立/銷毀、多份、可縮到零——**狀態必須外置**(DB、[物件儲存](../chapters/31-cloud-platform-deployment/06-managed-db-storage.md)、Redis),不能存本機磁碟或記憶體;要讀 `$PORT`、提供 `/health`。

**追問**:用 Little's Law 估實例數(在途 = rps × 延遲,async I/O-bound 提高並發省實例);託管 K8s 雲管控制平面、你管工作負載;HPA + Cluster Autoscaler 兩層擴縮;requests/limits 驅動排程與成本。

---

## Q4. Serverless(FaaS)適合什麼?冷啟動是什麼?何時不該用?

**考點**:Serverless([05-serverless](../chapters/31-cloud-platform-deployment/05-serverless.md))

**答**:FaaS(Lambda/Cloud Functions)適合**事件驅動、短任務、稀疏/突發流量**——上傳觸發、佇列消費、排程、webhook;閒置縮到零不收錢、來事件才啟動。

**冷啟動(cold start)**:沒有熱實例時(首次或擴容),雲要現起執行環境(配置 + 載 runtime + 載程式/依賴),造成延遲;緩解:精簡依賴、重初始化放 handler 外、設 provisioned concurrency/min instances。

**不該用**:**長任務**(撞執行時間上限)、**持續高流量**(可能比常駐容器貴且有冷啟動)——這時改用容器。

**追問**:成本 = 呼叫次數 + GB-秒;at-least-once → 處理要冪等;FaaS vs 容器界線(事件短任務 vs 常駐服務)。

---

## Q5. 為什麼運算要無狀態、狀態放託管服務?大檔為什麼進物件儲存?

**考點**:託管 DB 與物件儲存([06-managed-db-storage](../chapters/31-cloud-platform-deployment/06-managed-db-storage.md))

**答**:無狀態運算(容器/函式)隨時被建銷、多份,狀態要放**獨立、持久、可共享**的地方——**關聯式 DB(RDS/Cloud SQL)存結構化交易資料、物件儲存(S3/GCS)存大檔、Redis 存快取/session**。託管服務接手高可用/備份/修補。

**大檔進物件儲存、DB 只存 URL**:物件儲存**極便宜、耐久(11 個 9)、近乎無限**;塞進 DB 又貴又慢又難備份(成本可差數倍)。

**追問**:關聯式 DB 是常駐有狀態服務**不縮到零**;無伺服器多實例要用**連線池 / pooler(RDS Proxy/PgBouncer)** 否則打爆 DB 連線;大檔用**預簽 URL(presigned URL)** 讓客戶端直傳/直下、不經伺服器中轉;複製 ≠ 備份。

---

## Q6. 設定與密鑰差在哪?密鑰怎麼安全注入?資料庫為什麼要私有化?

**考點**:密鑰、設定與網路([07-secrets-config-network](../chapters/31-cloud-platform-deployment/07-secrets-config-network.md))

**答**:**設定**(log level、region)可放環境變數;**密鑰**(DB 密碼、API key)要**加密儲存 + 授權 + 稽核 + 輪替**——走密鑰管理服務(Secrets Manager / Secret Manager),**設定裡只放「引用位址」,執行期注入,絕不明文進版控/映像**。

**資料層私有化**:DB/快取放**私有子網、無公網 IP**,只讓應用連——縱深防禦(IAM 之外的獨立一層),避免公開 DB 被掃描爆破。

**追問**:密鑰以 KMS 加密、最小權限讀取、每次存取稽核;VPC + 公/私有子網 + 安全群組;VPC Endpoint / Private Service Connect 讓雲內流量不繞公網;CI 掃描寫死密鑰。

---

## Q7. IaC 是什麼?Terraform 的 state/plan/apply?為什麼要冪等?

**考點**:IaC / Terraform([08-iac-terraform](../chapters/31-cloud-platform-deployment/08-iac-terraform.md))

**答**:**IaC(基礎設施即程式碼)** 把「要哪些雲資源」寫成**宣告式程式碼**,取代手動點 console——可重現、可審查(PR)、可版控、防組態漂移,以程式碼為單一事實來源。

**Terraform 三概念**:**state**(記錄它管了哪些資源,是它的記憶)、**plan**(預演:顯示將 create/update/delete/no-op,不執行)、**apply**(執行變更並更新 state)。**冪等**:同一份程式碼 apply 多次結果一致,已符合的資源不重建——描述終態、重跑安全。

**追問**:state 要放**遠端 + 鎖**(S3+DynamoDB/GCS),絕不進版控;注意 replace(刪重建)對 DB 的破壞;AWS/GCP 各有 provider 但工作流(init/plan/apply)相同;module + variables 管多環境。

---

## Q8.(必考)OIDC 免金鑰部署是什麼?為什麼比長期金鑰安全?

**考點**:CI/CD 上雲([09-cicd-to-cloud](../chapters/31-cloud-platform-deployment/09-cicd-to-cloud.md))

**答**:傳統把長期 access key 存進 CI secret——**外洩重災區**(長期有效、易被竊/誤印)。**OIDC 聯合身分(federation)免金鑰**:CI 平台(GitHub)簽發**短時效 OIDC token**(內含 repo/branch claims)→ 雲驗證信任後**換發短時效臨時憑證** → CI 用它部署。**全程不存任何長期金鑰**。

**為什麼更安全**:**無靜態秘密可偷**、短時效(洩漏窗口小)、**強綁定 repo+branch**(別的 repo 拿不到)、可稽核。

**雲端驗證什麼**:簽發者(issuer)、audience、**subject(限定 `repo:org/name:ref:refs/heads/main`)**、有效期——通過才換發臨時憑證。**限定 repo + branch 是關鍵**。

**追問**:AWS `AssumeRoleWithWebIdentity` + OIDC provider vs GCP Workload Identity Federation;部署前品質門檻(test/lint/型別不過不部署)、版本化 tag 可回滾、prod 加審批/金絲雀;換到的部署身分要最小權限。

---

## Q9. SLO / error budget 是什麼?雲成本為什麼會失控、怎麼管?

**考點**:可觀測性與成本([10-observability-cost](../chapters/31-cloud-platform-deployment/10-observability-cost.md))

**答**:**SLI**(實測可靠性,如成功率 99.95%)、**SLO**(目標,如 ≥99.9%)、**error budget = 1 − SLO**(允許失敗量)。**還有預算 → 可衝新功能承擔風險;預算快用完 → 專注穩定性**——把可靠性變成可決策的數字。用 **burn rate**(多快燒完預算)告警,快/慢燃燒分別設閾值。

**雲成本會失控**:變動成本 + 自動擴縮無上限 + 忘關資源 + egress 傳輸費 + 選錯儲存類別 + 被灌爆。**怎麼管**:設**預算告警**(50/80/100%)+ **成本異常偵測**(今日 vs 基線突增)+ **標籤歸因**(按 team/env/service 分組)+ right-size + 擴縮設上限 + 關閒置。

**追問**:三支柱(logs/metrics/traces)雲上落地(CloudWatch/Cloud Monitoring),OTel 保可攜;看 p95/p99 而非平均(長尾);別把 SLO 訂成 100%(留 error budget 才能兼顧創新)。

---

## Q10. 描述把一個 Python 服務端到端部署上雲的完整架構與流程。

**考點**:Capstone([11-capstone-deploy](../chapters/31-cloud-platform-deployment/11-capstone-deploy.md))

**答**:**端到端架構**:

```text
git push → CI/CD(test/lint → build → OIDC 換臨時憑證 → push registry → deploy)
使用者 → 負載平衡 → Cloud Run/Fargate(無狀態,讀 $PORT、/health)
  ├─ 連線池 → Cloud SQL/RDS(結構化資料)
  ├─ 預簽 URL → GCS/S3(附件)
  └─ Redis(快取)
密鑰 ← Secret Manager 注入;身分 ← 最小權限 SA;DB/快取 ← 私有子網
全部由 Terraform 定義;Cloud Monitoring + SLO + 預算告警
```

**一次部署的資料流**:push → 品質門檻(pytest/ruff/mypy 不過就停)→ build 映像 → **OIDC 換短時效憑證(無長期金鑰)** → push registry → deploy → 密鑰注入 → 健康檢查 → 切流量(可金絲雀)→ 營運。

**追問**:安全問題是**硬 blocker**(密鑰寫死/DB 公開/CI 用長期金鑰/過度權限,一票否決);「生產級 vs 能跑」差在狀態外置、安全、免金鑰 CI、可觀測、成本管理;AWS↔GCP 服務對映;為何 task-api 用 Cloud Run/Fargate 而非 K8s。

---

⬅️ [Part 30](part30-production-ai.md) ｜ [回索引](README.md)

🎉 **完成全 31 Part 面試題庫!** 依 chapters 逐 Part 涵蓋語言核心 → 工程 → 資料 → AI → 雲端部署的高頻面試題,每題附「面試官想聽到的完整回答」與追問。
