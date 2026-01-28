"""
Diagnostics Module
Tests all API endpoints on connect to verify the backend is healthy.
Runs automatically when a session starts or credentials are saved.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st


@dataclass
class EndpointResult:
    """Result of a single endpoint diagnostic check."""
    name: str
    endpoint: str
    status: str  # 'ok', 'error', 'skipped'
    message: str = ""
    latency_ms: float = 0.0


@dataclass
class DiagnosticReport:
    """Full diagnostic report across all subsystems."""
    timestamp: str = ""
    backend: str = ""  # 'live' or 'demo'
    results: List[EndpointResult] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    skipped: int = 0

    @property
    def all_ok(self) -> bool:
        return self.failed == 0

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped


def run_diagnostics(api: Any, is_demo: bool = False) -> DiagnosticReport:
    """
    Run diagnostic checks against all API subsystems.

    Tests each endpoint with a lightweight read-only call to verify
    the backend is reachable and responding correctly.

    Args:
        api: API client (GenesysCloudAPI or DemoAPI)
        is_demo: Whether this is a demo backend

    Returns:
        DiagnosticReport with results for each endpoint
    """
    import time

    report = DiagnosticReport(
        timestamp=datetime.now().isoformat(),
        backend="demo" if is_demo else "live",
    )

    checks = [
        ("Users - List", "users.list_page", _check_users_list),
        ("Users - Search", "users.search", _check_users_search),
        ("Groups - List", "groups.list_page", _check_groups_list),
        ("Groups - Search", "groups.search", _check_groups_search),
        ("Queues - List", "queues.list_page", _check_queues_list),
        ("Queues - Search", "queues.search", _check_queues_search),
        ("Skills - List", "routing.list_skills_page", _check_skills_list),
        ("Skills - Get All", "routing.get_skills", _check_skills_all),
    ]

    for name, endpoint, check_fn in checks:
        start = time.time()
        try:
            ok, msg = check_fn(api)
            elapsed = (time.time() - start) * 1000
            result = EndpointResult(
                name=name,
                endpoint=endpoint,
                status="ok" if ok else "error",
                message=msg,
                latency_ms=round(elapsed, 1),
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            result = EndpointResult(
                name=name,
                endpoint=endpoint,
                status="error",
                message=str(e),
                latency_ms=round(elapsed, 1),
            )

        report.results.append(result)

    report.passed = sum(1 for r in report.results if r.status == "ok")
    report.failed = sum(1 for r in report.results if r.status == "error")
    report.skipped = sum(1 for r in report.results if r.status == "skipped")

    return report


def _check_users_list(api) -> tuple:
    resp = api.users.list_page(page_size=1, page_number=1)
    if resp.success:
        total = (resp.data or {}).get("total", 0)
        return True, f"{total} users available"
    return False, resp.error or "Failed"


def _check_users_search(api) -> tuple:
    results = api.users.search("a")
    if isinstance(results, list):
        return True, f"{len(results)} results"
    return False, "Search returned unexpected type"


def _check_groups_list(api) -> tuple:
    resp = api.groups.list_page(page_size=1, page_number=1)
    if resp.success:
        total = (resp.data or {}).get("total", 0)
        return True, f"{total} groups available"
    return False, resp.error or "Failed"


def _check_groups_search(api) -> tuple:
    results = api.groups.search("a")
    if isinstance(results, list):
        return True, f"{len(results)} results"
    return False, "Search returned unexpected type"


def _check_queues_list(api) -> tuple:
    resp = api.queues.list_page(page_size=1, page_number=1)
    if resp.success:
        total = (resp.data or {}).get("total", 0)
        return True, f"{total} queues available"
    return False, resp.error or "Failed"


def _check_queues_search(api) -> tuple:
    results = api.queues.search("a")
    if isinstance(results, list):
        return True, f"{len(results)} results"
    return False, "Search returned unexpected type"


def _check_skills_list(api) -> tuple:
    resp = api.routing.list_skills_page(page_size=1, page_number=1)
    if resp.success:
        total = (resp.data or {}).get("total", 0)
        return True, f"{total} skills available"
    return False, resp.error or "Failed"


def _check_skills_all(api) -> tuple:
    skills = api.routing.get_skills()
    if isinstance(skills, list):
        return True, f"{len(skills)} skills loaded"
    return False, "get_skills returned unexpected type"


def get_cached_report() -> Optional[DiagnosticReport]:
    """Retrieve cached diagnostic report from session state."""
    return st.session_state.get("_diagnostics_report")


def cache_report(report: DiagnosticReport) -> None:
    """Cache diagnostic report in session state."""
    st.session_state["_diagnostics_report"] = report


def clear_cached_report() -> None:
    """Clear cached diagnostic report."""
    st.session_state.pop("_diagnostics_report", None)


def render_diagnostics_summary(report: DiagnosticReport) -> None:
    """Render a compact diagnostics summary in Streamlit."""
    if report.all_ok:
        st.success(
            f"All {report.total} endpoints OK "
            f"({report.backend} backend)"
        )
    else:
        st.warning(
            f"{report.passed}/{report.total} endpoints OK, "
            f"{report.failed} failed "
            f"({report.backend} backend)"
        )

    with st.expander("Endpoint Details", expanded=not report.all_ok):
        for r in report.results:
            icon = "+" if r.status == "ok" else "-" if r.status == "error" else "?"
            latency = f" ({r.latency_ms:.0f}ms)" if r.latency_ms else ""
            status_text = f"[{icon}] {r.name}: {r.message}{latency}"
            if r.status == "ok":
                st.caption(status_text)
            elif r.status == "error":
                st.error(status_text)
            else:
                st.info(status_text)
