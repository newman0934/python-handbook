"""Part 19 範例的驗證測試。

執行：pytest examples/part19
"""

from __future__ import annotations

import json

from examples.part19.cloud_native import (
    AppState,
    DrainingServer,
    Metrics,
    SharedStore,
    Stage,
    StatelessInstance,
    health_check,
    multi_stage_size,
    prefork_dispatch,
    recommend_workers,
    reconcile,
    run_pipeline,
    single_stage_size,
    structured_log,
)


# --- Docker：健康檢查（見 01）---
def test_health_check() -> None:
    assert health_check(True, True)[0] == 200
    status, body = health_check(True, False)
    assert status == 503
    assert body["status"] == "unhealthy"


# --- 多階段建置：省下 build-only 元件（見 02）---
def test_image_size_reduction() -> None:
    assert single_stage_size() == 490
    assert multi_stage_size() == 220  # 排除 gcc(250) + libpq-dev(20)


# --- worker 配置（見 03）---
def test_recommend_workers() -> None:
    assert recommend_workers(8, io_bound=False) == 17  # 2*8+1
    assert recommend_workers(8, io_bound=True) == 8


def test_prefork_dispatch_balanced() -> None:
    assert prefork_dispatch(4, 100) == [25, 25, 25, 25]


# --- 12-factor：無狀態 session（見 04）---
def test_stateless_session_shared() -> None:
    store = SharedStore()
    a = StatelessInstance("A", store)
    b = StatelessInstance("B", store)
    a.login("sid-1", "alice")
    # 在 A 登入，B 也認得（可自由擴縮）
    assert b.whoami("sid-1") == "alice"


# --- CI/CD：fail-fast pipeline（見 05）---
def test_pipeline_fail_fast() -> None:
    ok, stopped = run_pipeline(
        [
            Stage("ruff", lambda: True),
            Stage("mypy", lambda: False),
            Stage("pytest", lambda: True),
        ]
    )
    assert ok is False
    assert stopped == "mypy"


def test_pipeline_all_pass() -> None:
    ok, _ = run_pipeline([Stage("ruff", lambda: True), Stage("pytest", lambda: True)])
    assert ok is True


# --- Kubernetes：探針與控制迴圈（見 06）---
def test_probes_liveness_vs_readiness() -> None:
    app = AppState()
    assert app.liveness() is True
    assert app.readiness() is False  # 尚未就緒
    app.started = True
    app.db_connected = True
    assert app.readiness() is True
    # DB 斷線：readiness 失敗但 liveness 仍 True（移出流量而非重啟）
    app.db_connected = False
    assert app.liveness() is True
    assert app.readiness() is False


def test_reconcile_scales_up_and_down() -> None:
    assert reconcile(3, ["pod-a"]) == ["pod-a", "pod-new-1", "pod-new-2"]
    assert reconcile(1, ["p1", "p2", "p3"]) == ["p1"]


# --- graceful shutdown：排空 in-flight（見 07）---
def test_graceful_drain() -> None:
    server = DrainingServer()
    for _ in range(3):
        assert server.handle_request() is True
    assert server.in_flight == 3
    server.on_sigterm()
    assert server.handle_request() is False  # 關閉中拒絕新請求
    assert server.drain() is True
    assert server.completed == 3
    assert server.rejected == 1


# --- 可觀測性：結構化日誌 + 指標（見 08）---
def test_structured_log_is_json_with_context() -> None:
    line = structured_log("ERROR", "payment_failed", "abc-1", order_id=123)
    parsed = json.loads(line)
    assert parsed["level"] == "ERROR"
    assert parsed["request_id"] == "abc-1"
    assert parsed["order_id"] == 123


def test_metrics_error_rate() -> None:
    m = Metrics()
    for status in (200, 200, 500):
        m.observe(status)
    assert m.requests_total == 3
    assert m.error_rate() == 1 / 3
