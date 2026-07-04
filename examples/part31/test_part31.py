"""Part 31 範例測試:雲端平台部署(AWS + GCP)。"""

from __future__ import annotations

import pytest

from examples.part31.cloud_deploy import (
    DeploymentPlan,
    Effect,
    FaaSPricing,
    Node,
    OIDCToken,
    Policy,
    Resource,
    ServiceConfig,
    Statement,
    TrustPolicy,
    apply_plan,
    audit_config,
    audit_deployment,
    authorize,
    choose_compute,
    choose_storage,
    db_monthly_cost,
    detect_cost_anomaly,
    equivalent,
    error_budget_status,
    estimate_instances,
    faas_monthly_cost,
    hpa_replicas,
    is_secret_ref,
    load_config,
    nodes_needed,
    object_storage_cost,
    plan,
    readiness_check,
    recommend_model,
    resolve_secret,
    verify_token,
)

# ---- ch01 ----


@pytest.mark.parametrize(
    "service, other",
    [
        ("Lambda", "Cloud Functions"),
        ("Cloud Run", "ECS/Fargate"),
        ("S3", "Cloud Storage"),
        ("RDS", "Cloud SQL"),
    ],
)
def test_equivalent_cross_cloud(service: str, other: str) -> None:
    _, resolved = equivalent(service)
    assert resolved == other


def test_equivalent_unknown() -> None:
    assert equivalent("NonexistentService") == (None, None)


@pytest.mark.parametrize(
    "needs, expected",
    [
        ({"event_driven": True, "short_tasks": True}, "serverless"),
        ({"stateless_http": True}, "container"),
        ({"complex_orchestration": True}, "managed-k8s"),
        ({}, "vm"),
    ],
)
def test_recommend_model(needs: dict[str, bool], expected: str) -> None:
    assert recommend_model(needs) == expected


# ---- ch02 IAM ----


def _sample_policy() -> Policy:
    return Policy(
        [
            Statement(
                Effect.ALLOW,
                frozenset({"s3:GetObject", "s3:PutObject"}),
                frozenset({"arn:aws:s3:::app-bucket/*"}),
            ),
            Statement(
                Effect.DENY,
                frozenset({"s3:DeleteObject"}),
                frozenset({"arn:aws:s3:::app-bucket/*"}),
            ),
        ]
    )


def test_authorize_allow() -> None:
    assert authorize(_sample_policy(), "s3:GetObject", "arn:aws:s3:::app-bucket/f.txt") is True


def test_authorize_explicit_deny_wins() -> None:
    assert authorize(_sample_policy(), "s3:DeleteObject", "arn:aws:s3:::app-bucket/f.txt") is False


def test_authorize_default_deny() -> None:
    assert authorize(_sample_policy(), "ec2:StartInstances", "*") is False
    assert authorize(_sample_policy(), "s3:GetObject", "arn:aws:s3:::other/x") is False


def test_authorize_wildcard_action() -> None:
    pol = Policy([Statement(Effect.ALLOW, frozenset({"s3:*"}), frozenset({"*"}))])
    assert authorize(pol, "s3:GetObject", "anything") is True


def test_deny_wildcard_beats_allow() -> None:
    pol = Policy(
        [
            Statement(Effect.ALLOW, frozenset({"*"}), frozenset({"*"})),
            Statement(Effect.DENY, frozenset({"iam:*"}), frozenset({"*"})),
        ]
    )
    assert authorize(pol, "s3:GetObject", "x") is True
    assert authorize(pol, "iam:DeleteRole", "x") is False


# ---- ch03 容器 ----


def test_readiness_check_ok() -> None:
    good = ServiceConfig(True, True, True, True, True, 1.0, 512)
    assert readiness_check(good) == []


def test_readiness_check_problems() -> None:
    bad = ServiceConfig(True, False, False, False, True, 1.0, 128)
    problems = readiness_check(bad)
    assert len(problems) == 4


@pytest.mark.parametrize(
    "rps, latency, conc, expected",
    [
        (10, 0.2, 80, 1),
        (100, 0.2, 80, 1),
        (500, 0.2, 80, 2),
        (4000, 0.2, 80, 10),
    ],
)
def test_estimate_instances(rps: float, latency: float, conc: int, expected: int) -> None:
    assert estimate_instances(rps, latency, conc) == expected


def test_estimate_instances_min_one() -> None:
    assert estimate_instances(0, 0.2, 80) == 1


def test_estimate_instances_invalid_concurrency() -> None:
    with pytest.raises(ValueError):
        estimate_instances(10, 0.2, 0)


# ---- ch04 K8s ----


@pytest.mark.parametrize(
    "util, expected",
    [
        (0.30, 3),
        (0.50, 4),
        (0.90, 8),
    ],
)
def test_hpa_replicas(util: float, expected: int) -> None:
    assert hpa_replicas(4, util, 0.50, 20) == expected


def test_hpa_replicas_capped() -> None:
    assert hpa_replicas(4, 5.0, 0.50, 20) == 20  # 夾在 max


def test_hpa_replicas_invalid_target() -> None:
    with pytest.raises(ValueError):
        hpa_replicas(4, 0.5, 0.0, 20)


@pytest.mark.parametrize(
    "replicas, expected",
    [
        (3, 1),
        (10, 3),
        (30, 8),
    ],
)
def test_nodes_needed(replicas: int, expected: int) -> None:
    node = Node(cpu_milli=2000, mem_mb=4096)
    assert nodes_needed(500, 512, replicas, node) == expected


def test_nodes_needed_pod_too_big() -> None:
    node = Node(cpu_milli=1000, mem_mb=1024)
    with pytest.raises(ValueError):
        nodes_needed(4000, 512, 3, node)


# ---- ch05 FaaS ----


def test_faas_cost_sparse_cheap() -> None:
    pricing = FaaSPricing(0.20, 0.0000166667)
    assert faas_monthly_cost(10_000, 0.2, 0.5, pricing) < 0.02


def test_faas_cost_scales_with_usage() -> None:
    pricing = FaaSPricing(0.20, 0.0000166667)
    low = faas_monthly_cost(1_000_000, 0.2, 0.5, pricing)
    high = faas_monthly_cost(50_000_000, 0.2, 0.5, pricing)
    assert high > low > 0


@pytest.mark.parametrize(
    "ev, dur, sparse, expected",
    [
        (True, 2.0, True, "faas"),
        (True, 600.0, True, "container"),  # 超過執行上限
        (False, 0.1, False, "container"),  # 持續高流量
    ],
)
def test_choose_compute(ev: bool, dur: float, sparse: bool, expected: str) -> None:
    assert choose_compute(ev, dur, sparse) == expected


# ---- ch06 儲存 ----


@pytest.mark.parametrize(
    "s, t, b, c, expected",
    [
        (True, True, False, False, "relational-db"),
        (False, False, True, False, "object-storage"),
        (False, False, False, True, "cache"),
        (False, False, False, False, "nosql"),
    ],
)
def test_choose_storage(s: bool, t: bool, b: bool, c: bool, expected: str) -> None:
    assert choose_storage(s, t, b, c) == expected


def test_large_binary_prefers_object_storage() -> None:
    # 即使結構化,large_binary 優先走物件儲存
    assert choose_storage(True, True, True, False) == "object-storage"


def test_object_storage_far_cheaper_than_db() -> None:
    obj = object_storage_cost(1000, 0.023)
    db = db_monthly_cost(0.10, 1000, 0.115)
    assert obj < db
    assert db / obj > 5  # 差數倍


# ---- ch07 設定/密鑰 ----


def test_load_config_precedence() -> None:
    cfg = load_config(
        {"LOG_LEVEL": "INFO", "REGION": "us"},
        {"LOG_LEVEL": "WARNING"},
        {"REGION": "asia"},
    )
    assert cfg["LOG_LEVEL"] == "WARNING"  # 設定檔覆蓋預設
    assert cfg["REGION"] == "asia"  # 環境覆蓋預設


@pytest.mark.parametrize(
    "value, expected",
    [
        ("projects/p/secrets/db:latest", True),
        ("arn:aws:secretsmanager:us:1:secret:db", True),
        ("secret://vault/db", True),
        ("plaintext123", False),
    ],
)
def test_is_secret_ref(value: str, expected: bool) -> None:
    assert is_secret_ref(value) is expected


def test_resolve_secret() -> None:
    vault = {"db-password": "s3cr3t"}
    assert resolve_secret("projects/p/secrets/db-password:latest", vault) == "s3cr3t"


def test_resolve_secret_rejects_plaintext() -> None:
    with pytest.raises(ValueError):
        resolve_secret("plaintext", {})


def test_resolve_secret_missing() -> None:
    with pytest.raises(KeyError):
        resolve_secret("secret://vault/nope", {"other": "x"})


def test_audit_config_flags_plaintext_secret() -> None:
    warnings = audit_config({"DB_PASSWORD": "hardcoded", "LOG_LEVEL": "INFO"})
    assert len(warnings) == 1
    assert "DB_PASSWORD" in warnings[0]


def test_audit_config_accepts_secret_ref() -> None:
    warnings = audit_config({"DB_PASSWORD": "projects/p/secrets/db:latest"})
    assert warnings == []


# ---- ch08 IaC reconcile ----


def test_plan_create_update_noop_delete() -> None:
    current = {
        "a": Resource("a", (("v", "off"),)),
        "b": Resource("b", (("v", "1"),)),
        "gone": Resource("gone", ()),
    }
    desired = {
        "a": Resource("a", (("v", "on"),)),  # update
        "b": Resource("b", (("v", "1"),)),  # no-op
        "c": Resource("c", ()),  # create
    }
    actions = plan(desired, current)
    assert "update:a" in actions
    assert "no-op:b" in actions
    assert "create:c" in actions
    assert "delete:gone" in actions


def test_plan_idempotent_after_apply() -> None:
    desired = {"a": Resource("a", (("v", "on"),))}
    new_state = apply_plan(desired)
    actions = plan(desired, new_state)
    assert actions == ["no-op:a"]


# ---- ch09 OIDC ----


def _policy() -> TrustPolicy:
    return TrustPolicy(
        trusted_issuer="https://token.actions.githubusercontent.com",
        expected_audience="sts.amazonaws.com",
        allowed_sub_prefix="repo:myorg/task-api:ref:refs/heads/main",
    )


def _token(**kw: object) -> OIDCToken:
    base = {
        "iss": "https://token.actions.githubusercontent.com",
        "aud": "sts.amazonaws.com",
        "sub": "repo:myorg/task-api:ref:refs/heads/main",
        "exp": 1_000_000.0 + 300,
    }
    base.update(kw)
    return OIDCToken(**base)  # type: ignore[arg-type]


def test_oidc_valid_token() -> None:
    ok, reason = verify_token(_token(), _policy(), now=1_000_000.0)
    assert ok is True
    assert reason == "ok"


def test_oidc_wrong_repo_denied() -> None:
    tok = _token(sub="repo:attacker/evil:ref:refs/heads/main")
    ok, reason = verify_token(tok, _policy(), now=1_000_000.0)
    assert ok is False
    assert reason == "subject-not-allowed"


def test_oidc_wrong_branch_denied() -> None:
    tok = _token(sub="repo:myorg/task-api:ref:refs/heads/dev")
    ok, _ = verify_token(tok, _policy(), now=1_000_000.0)
    assert ok is False


def test_oidc_expired_denied() -> None:
    tok = _token(exp=1_000_000.0 - 10)
    ok, reason = verify_token(tok, _policy(), now=1_000_000.0)
    assert ok is False
    assert reason == "token-expired"


def test_oidc_untrusted_issuer() -> None:
    tok = _token(iss="https://evil.example.com")
    ok, reason = verify_token(tok, _policy(), now=1_000_000.0)
    assert ok is False
    assert reason == "issuer-untrusted"


def test_oidc_wrong_audience() -> None:
    tok = _token(aud="wrong-audience")
    ok, reason = verify_token(tok, _policy(), now=1_000_000.0)
    assert ok is False
    assert reason == "audience-mismatch"


# ---- ch10 SLO / 成本 ----


def test_error_budget_within() -> None:
    s = error_budget_status(0.999, 1_000_000, 500)
    assert s["allowed_failures"] == 1000.0
    assert s["budget_consumed_pct"] == 50.0
    assert s["within_slo"] == 1.0


def test_error_budget_exceeded() -> None:
    s = error_budget_status(0.999, 1_000_000, 2500)
    assert s["budget_consumed_pct"] == 250.0
    assert s["within_slo"] == 0.0


@pytest.mark.parametrize(
    "today, fire",
    [
        (110.0, False),
        (180.0, True),
        (320.0, True),
    ],
)
def test_detect_cost_anomaly(today: float, fire: bool) -> None:
    triggered, _ = detect_cost_anomaly(100.0, today, 50.0)
    assert triggered is fire


def test_detect_cost_anomaly_zero_baseline() -> None:
    triggered, inc = detect_cost_anomaly(0.0, 100.0, 50.0)
    assert triggered is False
    assert inc == 0.0


# ---- ch11 端到端驗收 ----


def test_deployment_ready() -> None:
    ok, failed, blockers = audit_deployment(DeploymentPlan())
    assert ok is True
    assert failed == []
    assert blockers == []


def test_deployment_security_blocker_stops_prod() -> None:
    risky = DeploymentPlan(
        secrets_via_manager=False,
        db_private_network=False,
        budget_alerts=False,
    )
    ok, failed, blockers = audit_deployment(risky)
    assert ok is False
    assert "secrets_via_manager" in blockers
    assert "db_private_network" in blockers
    assert "budget_alerts" in failed
    assert "budget_alerts" not in blockers  # 非安全 blocker


def test_deployment_nonsecurity_gap_still_blocks_full_readiness() -> None:
    plan_obj = DeploymentPlan(immutable_image_tag=False)
    ok, failed, blockers = audit_deployment(plan_obj)
    assert ok is False
    assert failed == ["immutable_image_tag"]
    assert blockers == []
