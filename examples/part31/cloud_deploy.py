"""Part 31:雲端平台部署(AWS + GCP)可執行範例。

集中前十章的核心邏輯,全部使用純標準庫、可離線測試(不需雲帳號):

- ch01 服務對照與部署模型選型
- ch02 IAM 授權引擎(default deny + explicit deny 優先)
- ch03 容器部署就緒度 + 擴縮估算
- ch04 K8s HPA 副本估算 + 節點裝箱
- ch05 FaaS 成本模型 + FaaS/容器選型
- ch06 儲存選型 + 成本對照
- ch07 設定優先序 + 密鑰引用解析 + 稽核
- ch08 迷你宣告式 reconcile(模擬 terraform plan)
- ch09 OIDC 信任驗證
- ch10 SLO/error budget + 成本異常偵測
- ch11 端到端部署就緒度總驗收
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum

# ---------------------------------------------------------------------------
# ch01:AWS/GCP 服務對照 + 部署模型選型
# ---------------------------------------------------------------------------

SERVICE_MAP: dict[str, tuple[str, str]] = {
    "vm-iaas": ("EC2", "Compute Engine"),
    "container-caas": ("ECS/Fargate", "Cloud Run"),
    "managed-k8s": ("EKS", "GKE"),
    "function-faas": ("Lambda", "Cloud Functions"),
    "sql-db": ("RDS", "Cloud SQL"),
    "object-storage": ("S3", "Cloud Storage"),
    "secrets": ("Secrets Manager", "Secret Manager"),
    "registry": ("ECR", "Artifact Registry"),
    "monitoring": ("CloudWatch", "Cloud Monitoring"),
}


def equivalent(service: str) -> tuple[str | None, str | None]:
    """給任一雲的服務名,查另一雲對應。回 (概念, 另一雲服務)。"""
    s = service.lower()
    for concept, (aws, gcp) in SERVICE_MAP.items():
        if s in aws.lower():
            return concept, gcp
        if s in gcp.lower():
            return concept, aws
    return None, None


def recommend_model(needs: dict[str, bool]) -> str:
    """依需求推薦部署模型。"""
    if needs.get("event_driven") and needs.get("short_tasks"):
        return "serverless"
    if needs.get("stateless_http") and not needs.get("complex_orchestration"):
        return "container"
    if needs.get("complex_orchestration"):
        return "managed-k8s"
    return "vm"


# ---------------------------------------------------------------------------
# ch02:IAM 授權引擎
# ---------------------------------------------------------------------------


class Effect(Enum):
    ALLOW = "Allow"
    DENY = "Deny"


@dataclass(frozen=True)
class Statement:
    effect: Effect
    actions: frozenset[str]
    resources: frozenset[str]


@dataclass
class Policy:
    statements: list[Statement] = field(default_factory=list)


def _matches(pattern: str, value: str) -> bool:
    if pattern == "*":
        return True
    if pattern.endswith("*"):
        return value.startswith(pattern[:-1])
    return pattern == value


def _statement_applies(stmt: Statement, action: str, resource: str) -> bool:
    action_ok = any(_matches(a, action) for a in stmt.actions)
    resource_ok = any(_matches(r, resource) for r in stmt.resources)
    return action_ok and resource_ok


def authorize(policy: Policy, action: str, resource: str) -> bool:
    """default deny;explicit deny 勝過 allow。"""
    allowed = False
    for stmt in policy.statements:
        if not _statement_applies(stmt, action, resource):
            continue
        if stmt.effect is Effect.DENY:
            return False
        allowed = True
    return allowed


# ---------------------------------------------------------------------------
# ch03:容器部署就緒度 + 擴縮估算
# ---------------------------------------------------------------------------


@dataclass
class ServiceConfig:
    has_dockerfile: bool
    listens_on_port_env: bool
    stateless: bool
    health_endpoint: bool
    secrets_from_env: bool
    cpu: float
    memory_mb: int


def readiness_check(cfg: ServiceConfig) -> list[str]:
    problems: list[str] = []
    if not cfg.has_dockerfile:
        problems.append("缺 Dockerfile / buildpack 來源")
    if not cfg.listens_on_port_env:
        problems.append("未讀取 $PORT")
    if not cfg.stateless:
        problems.append("非無狀態:狀態需外置")
    if not cfg.health_endpoint:
        problems.append("缺 /health 健康檢查端點")
    if not cfg.secrets_from_env:
        problems.append("密鑰寫死")
    if cfg.memory_mb < 256:
        problems.append("記憶體過低(<256MB)")
    return problems


def estimate_instances(peak_rps: float, avg_latency_s: float, concurrency: int) -> int:
    """Little's Law:在途請求 = rps × 延遲;實例 = ceil(在途 / 並發)。"""
    if concurrency <= 0:
        raise ValueError("concurrency 須 > 0")
    in_flight = peak_rps * avg_latency_s
    return max(1, math.ceil(in_flight / concurrency))


# ---------------------------------------------------------------------------
# ch04:K8s HPA + 節點裝箱
# ---------------------------------------------------------------------------


def hpa_replicas(
    current_replicas: int, current_cpu_util: float, target_cpu_util: float, max_replicas: int
) -> int:
    if target_cpu_util <= 0:
        raise ValueError("target 使用率須 > 0")
    desired = math.ceil(current_replicas * (current_cpu_util / target_cpu_util))
    return max(1, min(desired, max_replicas))


@dataclass
class Node:
    cpu_milli: int
    mem_mb: int


def nodes_needed(pod_cpu_milli: int, pod_mem_mb: int, replicas: int, node: Node) -> int:
    per_node_by_cpu = node.cpu_milli // pod_cpu_milli
    per_node_by_mem = node.mem_mb // pod_mem_mb
    pods_per_node = min(per_node_by_cpu, per_node_by_mem)
    if pods_per_node < 1:
        raise ValueError("單一 Pod 的 requests 超過節點容量")
    return math.ceil(replicas / pods_per_node)


# ---------------------------------------------------------------------------
# ch05:FaaS 成本模型 + 選型
# ---------------------------------------------------------------------------


@dataclass
class FaaSPricing:
    per_million_requests: float
    per_gb_second: float


def faas_monthly_cost(
    invocations: int, avg_duration_s: float, memory_gb: float, pricing: FaaSPricing
) -> float:
    request_cost = (invocations / 1_000_000) * pricing.per_million_requests
    gb_seconds = invocations * avg_duration_s * memory_gb
    compute_cost = gb_seconds * pricing.per_gb_second
    return round(request_cost + compute_cost, 4)


def choose_compute(event_driven: bool, avg_duration_s: float, sparse_traffic: bool) -> str:
    if avg_duration_s > 300:
        return "container"
    if event_driven and sparse_traffic:
        return "faas"
    if not sparse_traffic:
        return "container"
    return "either"


# ---------------------------------------------------------------------------
# ch06:儲存選型 + 成本對照
# ---------------------------------------------------------------------------


def choose_storage(
    structured: bool, transactional: bool, large_binary: bool, needs_cache: bool
) -> str:
    if large_binary:
        return "object-storage"
    if needs_cache:
        return "cache"
    if structured and transactional:
        return "relational-db"
    if structured:
        return "relational-or-nosql"
    return "nosql"


def object_storage_cost(gb: float, per_gb_month: float) -> float:
    return round(gb * per_gb_month, 2)


def db_monthly_cost(
    instance_usd_per_hour: float, storage_gb: float, storage_per_gb: float
) -> float:
    instance = instance_usd_per_hour * 24 * 30
    storage = storage_gb * storage_per_gb
    return round(instance + storage, 2)


# ---------------------------------------------------------------------------
# ch07:設定優先序 + 密鑰引用
# ---------------------------------------------------------------------------


def load_config(
    defaults: dict[str, str], file_cfg: dict[str, str], env: dict[str, str]
) -> dict[str, str]:
    merged = dict(defaults)
    merged.update(file_cfg)
    merged.update(env)
    return merged


def is_secret_ref(value: str) -> bool:
    return value.startswith(("secret://", "arn:aws:secretsmanager:", "projects/"))


def resolve_secret(ref: str, vault: dict[str, str]) -> str:
    if not is_secret_ref(ref):
        raise ValueError(f"不是合法的密鑰引用: {ref!r}")
    key = ref.split("/")[-1].split(":")[0]
    if key not in vault:
        raise KeyError(f"密鑰不存在: {key}")
    return vault[key]


def audit_config(cfg: dict[str, str]) -> list[str]:
    warnings: list[str] = []
    suspicious = ("password", "secret", "token", "api_key", "private_key")
    for k, v in cfg.items():
        if any(s in k.lower() for s in suspicious) and not is_secret_ref(v):
            warnings.append(f"{k} 疑似明文密鑰")
    return warnings


# ---------------------------------------------------------------------------
# ch08:迷你宣告式 reconcile
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Resource:
    name: str
    attrs: tuple[tuple[str, str], ...]


def plan(desired: dict[str, Resource], current: dict[str, Resource]) -> list[str]:
    actions: list[str] = []
    for name, want in desired.items():
        if name not in current:
            actions.append(f"create:{name}")
        elif current[name].attrs != want.attrs:
            actions.append(f"update:{name}")
        else:
            actions.append(f"no-op:{name}")
    for name in current:
        if name not in desired:
            actions.append(f"delete:{name}")
    return actions


def apply_plan(desired: dict[str, Resource]) -> dict[str, Resource]:
    return dict(desired)


# ---------------------------------------------------------------------------
# ch09:OIDC 信任驗證
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OIDCToken:
    iss: str
    aud: str
    sub: str
    exp: float


@dataclass(frozen=True)
class TrustPolicy:
    trusted_issuer: str
    expected_audience: str
    allowed_sub_prefix: str


def verify_token(
    token: OIDCToken, policy: TrustPolicy, now: float | None = None
) -> tuple[bool, str]:
    now = time.time() if now is None else now
    if token.iss != policy.trusted_issuer:
        return False, "issuer-untrusted"
    if token.aud != policy.expected_audience:
        return False, "audience-mismatch"
    if not token.sub.startswith(policy.allowed_sub_prefix):
        return False, "subject-not-allowed"
    if token.exp < now:
        return False, "token-expired"
    return True, "ok"


# ---------------------------------------------------------------------------
# ch10:SLO / error budget + 成本異常偵測
# ---------------------------------------------------------------------------


def error_budget_status(slo: float, total_requests: int, failed_requests: int) -> dict[str, float]:
    budget_fraction = 1 - slo
    allowed_failures = total_requests * budget_fraction
    actual_fraction = failed_requests / total_requests if total_requests else 0.0
    consumed = (failed_requests / allowed_failures) if allowed_failures else 0.0
    return {
        "allowed_failures": round(allowed_failures, 1),
        "actual_failures": float(failed_requests),
        "actual_failure_pct": round(actual_fraction * 100, 4),
        "budget_consumed_pct": round(consumed * 100, 1),
        "within_slo": float(failed_requests <= allowed_failures),
    }


def detect_cost_anomaly(
    baseline_daily: float, today: float, threshold_pct: float
) -> tuple[bool, float]:
    if baseline_daily <= 0:
        return False, 0.0
    increase_pct = (today - baseline_daily) / baseline_daily * 100
    return increase_pct > threshold_pct, round(increase_pct, 1)


# ---------------------------------------------------------------------------
# ch11:端到端部署就緒度總驗收
# ---------------------------------------------------------------------------

SECURITY_BLOCKERS = {
    "dedicated_least_priv_sa",
    "secrets_via_manager",
    "db_private_network",
    "cicd_oidc_keyless",
}


@dataclass
class DeploymentPlan:
    stateless: bool = True
    reads_port_env: bool = True
    health_endpoint: bool = True
    immutable_image_tag: bool = True
    autoscale_max_set: bool = True
    db_uses_pool: bool = True
    files_in_object_storage: bool = True
    backups_verified: bool = True
    dedicated_least_priv_sa: bool = True
    secrets_via_manager: bool = True
    db_private_network: bool = True
    terraform_managed: bool = True
    cicd_oidc_keyless: bool = True
    quality_gate_before_deploy: bool = True
    monitoring_and_alerts: bool = True
    budget_alerts: bool = True


def audit_deployment(plan_obj: DeploymentPlan) -> tuple[bool, list[str], list[str]]:
    """回 (可否上 prod, 未過項目, 其中安全 blocker)。"""
    checks = vars(plan_obj)
    failed = [name for name, ok in checks.items() if not ok]
    blockers = [name for name in failed if name in SECURITY_BLOCKERS]
    return len(failed) == 0, failed, blockers


def main() -> None:  # pragma: no cover - 手動示範用
    print("ch01 對照:", equivalent("Lambda"))
    print("ch01 選型:", recommend_model({"stateless_http": True}))
    print("ch03 實例估算:", estimate_instances(500, 0.2, 80))
    print("ch10 error budget:", error_budget_status(0.999, 1_000_000, 2500)["budget_consumed_pct"])
    ok, failed, blockers = audit_deployment(DeploymentPlan())
    print("ch11 就緒:", ok, "未過:", failed, "blocker:", blockers)


if __name__ == "__main__":
    main()
