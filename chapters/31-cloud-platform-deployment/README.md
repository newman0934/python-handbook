# Part 31：雲端平台部署 Cloud Platform Deployment(AWS + GCP)

> [Part 19 雲原生](../19-cloud-native/README.md)教的是**廠商中立**的基礎(Docker、K8s、12-factor)——學會了「哪個雲都能跑」。這一 Part 把它落地到**兩大雲的實際部署**:AWS 與 GCP。每章都以 **AWS ↔ GCP 對照**呈現(同一個概念在兩雲叫什麼、怎麼用),讓你不被單一雲綁死,並能在兩者間遷移與選型。貫穿的實例是全書的 [task-api](../../project/) 專案——把它端到端部署上雲。

> 🧭 延伸自 [Part 19 雲原生](../19-cloud-native/README.md)。範例用**純 Python 可測輔助**(服務對照、成本估算、IAM 檢查、部署就緒度),真實的 CLI / Terraform / YAML 以**示意**呈現(CI 不需雲帳號)。假設你已會 [Docker/K8s](../19-cloud-native/README.md)。

## 章節

| 章 | 標題 |
|----|------|
| 01 | [雲端部署概論與 AWS/GCP 對照](01-cloud-overview.md) |
| 02 | [IAM:身分與存取管理](02-iam.md) |
| 03 | [容器部署:ECS/Fargate vs Cloud Run](03-containers-ecs-cloudrun.md) |
| 04 | [託管 Kubernetes:EKS vs GKE](04-managed-k8s.md) |
| 05 | [Serverless:Lambda vs Cloud Functions](05-serverless.md) |
| 06 | [託管資料庫與物件儲存](06-managed-db-storage.md) |
| 07 | [密鑰、設定與網路](07-secrets-config-network.md) |
| 08 | [IaC:Terraform 多雲](08-iac-terraform.md) |
| 09 | [CI/CD 上雲(OIDC 免金鑰)](09-cicd-to-cloud.md) |
| 10 | [可觀測性與成本管理](10-observability-cost.md) |
| 11 | [🏗️ Capstone:task-api 端到端上雲](11-capstone-deploy.md) |

---

⬅️ 相關：[Part 19 雲原生與部署](../19-cloud-native/README.md)

[⬆️ 回章節總覽](../README.md)
