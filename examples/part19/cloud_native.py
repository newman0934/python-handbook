"""Part 19 雲原生與部署範例：健康檢查 / 映像大小 / worker 配置 /
無狀態 / CI pipeline / K8s 探針 / 優雅關閉 / 可觀測性。

全部純 stdlib，封裝可驗證的確定性邏輯。
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


# ===== Docker：健康檢查（見 01）=====
def health_check(db_ok: bool, cache_ok: bool) -> tuple[int, dict[str, object]]:
    """所有依賴健康才回 200，否則 503。"""
    checks = {"database": db_ok, "cache": cache_ok}
    healthy = all(checks.values())
    status = 200 if healthy else 503
    return status, {"status": "healthy" if healthy else "unhealthy", "checks": checks}


# ===== 多階段建置：映像大小估算（見 02）=====
@dataclass(frozen=True)
class Component:
    name: str
    size_mb: int
    build_only: bool


_COMPONENTS = [
    Component("python:3.12-slim", 130, build_only=False),
    Component("gcc + dev tools", 250, build_only=True),
    Component("libpq-dev", 20, build_only=True),
    Component("libpq5", 5, build_only=False),
    Component("compiled deps", 80, build_only=False),
    Component("app code", 5, build_only=False),
]


def single_stage_size() -> int:
    return sum(c.size_mb for c in _COMPONENTS)


def multi_stage_size() -> int:
    return sum(c.size_mb for c in _COMPONENTS if not c.build_only)


# ===== Gunicorn/Uvicorn：worker 配置（見 03）=====
def recommend_workers(cpu_count: int, io_bound: bool) -> int:
    """CPU-bound/同步: 2*cpu+1；I/O-bound/非同步: 約 = cpu。"""
    if io_bound:
        return max(2, cpu_count)
    return 2 * cpu_count + 1


def prefork_dispatch(num_workers: int, num_requests: int) -> list[int]:
    """round-robin 分派請求給 worker，回傳每 worker 處理數。"""
    handled = [0] * num_workers
    for i in range(num_requests):
        handled[i % num_workers] += 1
    return handled


# ===== 12-factor：無狀態 session（見 04）=====
class SharedStore:
    """共享後端服務（Redis/DB 模擬）。"""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def get(self, key: str) -> str | None:
        return self._data.get(key)


class StatelessInstance:
    """無狀態實例：session 存共享後端，任一實例都能處理任一請求。"""

    def __init__(self, name: str, store: SharedStore) -> None:
        self.name = name
        self._store = store

    def login(self, sid: str, user: str) -> None:
        self._store.set(f"session:{sid}", user)

    def whoami(self, sid: str) -> str | None:
        return self._store.get(f"session:{sid}")


# ===== CI/CD：fail-fast pipeline（見 05）=====
@dataclass
class Stage:
    name: str
    check: Callable[[], bool]


def run_pipeline(stages: list[Stage]) -> tuple[bool, str]:
    """依序執行，任一失敗即中止（fail fast）。回傳 (是否通過, 停在哪)。"""
    for stage in stages:
        if not stage.check():
            return False, stage.name
    return True, "全部通過"


# ===== Kubernetes：探針與控制迴圈（見 06）=====
class AppState:
    def __init__(self) -> None:
        self.started = False
        self.db_connected = False

    def liveness(self) -> bool:
        """存活：行程本身有回應（不檢查外部依賴）。"""
        return True

    def readiness(self) -> bool:
        """就緒：啟動完成且依賴可用。"""
        return self.started and self.db_connected


def reconcile(desired: int, healthy_pods: list[str]) -> list[str]:
    """控制迴圈：讓副本數趨近期望值。"""
    result = list(healthy_pods)
    actual = len(result)
    if actual < desired:
        result.extend(f"pod-new-{i}" for i in range(actual, desired))
    elif actual > desired:
        result = result[:desired]
    return result


# ===== graceful shutdown：排空 in-flight 請求（見 07）=====
class DrainingServer:
    def __init__(self) -> None:
        self.accepting = True
        self.in_flight = 0
        self.completed = 0
        self.rejected = 0

    def handle_request(self) -> bool:
        """受理請求；關閉中則拒絕。回傳是否受理。"""
        if not self.accepting:
            self.rejected += 1
            return False
        self.in_flight += 1
        return True

    def finish_request(self) -> None:
        if self.in_flight > 0:
            self.in_flight -= 1
            self.completed += 1

    def on_sigterm(self) -> None:
        """收到 SIGTERM：先停收新請求。"""
        self.accepting = False

    def drain(self) -> bool:
        """等 in-flight 全部完成才算優雅關閉成功。"""
        while self.in_flight > 0:
            self.finish_request()
        return self.in_flight == 0


# ===== 可觀測性：結構化日誌 + 指標（見 08）=====
def structured_log(level: str, event: str, request_id: str, **fields: object) -> str:
    """輸出一行結構化 JSON 日誌。"""
    record = {"level": level, "event": event, "request_id": request_id, **fields}
    return json.dumps(record, ensure_ascii=False, sort_keys=True)


@dataclass
class Metrics:
    requests_total: int = 0
    by_status: Counter[int] = field(default_factory=Counter)

    def observe(self, status: int) -> None:
        self.requests_total += 1
        self.by_status[status] += 1

    def error_rate(self) -> float:
        errors = sum(n for s, n in self.by_status.items() if s >= 500)
        return errors / self.requests_total if self.requests_total else 0.0
