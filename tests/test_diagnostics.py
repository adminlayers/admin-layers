"""Tests for core.diagnostics — endpoint health checks."""

from core.demo import DemoAPI
from core.diagnostics import run_diagnostics


class TestDiagnostics:
    def test_all_checks_pass_on_demo(self):
        api = DemoAPI()
        report = run_diagnostics(api, is_demo=True)
        assert report.all_ok
        assert report.passed == report.total
        assert report.failed == 0
        assert report.backend == "demo"

    def test_report_has_all_endpoints(self):
        api = DemoAPI()
        report = run_diagnostics(api, is_demo=True)
        names = {r.name for r in report.results}
        assert "Users - List" in names
        assert "Groups - List" in names
        assert "Queues - List" in names
        assert "Skills - List" in names

    def test_report_timestamp(self):
        api = DemoAPI()
        report = run_diagnostics(api, is_demo=True)
        assert report.timestamp != ""

    def test_broken_api_reports_errors(self):
        class BrokenAPI:
            class users:
                @staticmethod
                def list_page(page_size=25, page_number=1):
                    raise RuntimeError("connection failed")

                @staticmethod
                def search(query):
                    return []

            class groups:
                @staticmethod
                def list_page(page_size=25, page_number=1):
                    raise RuntimeError("connection failed")

                @staticmethod
                def search(query):
                    return []

            class queues:
                @staticmethod
                def list_page(page_size=25, page_number=1):
                    raise RuntimeError("connection failed")

                @staticmethod
                def search(query):
                    return []

            class routing:
                @staticmethod
                def list_skills_page(page_size=25, page_number=1):
                    raise RuntimeError("connection failed")

                @staticmethod
                def get_skills():
                    return []

        report = run_diagnostics(BrokenAPI(), is_demo=False)
        assert not report.all_ok
        assert report.failed > 0
        assert report.backend == "live"
