"""Tests for core.services — backend interface validation."""

from core.demo import DemoAPI
from core.services import validate_backend


class TestValidateBackend:
    def test_demo_api_passes(self):
        api = DemoAPI()
        errors = validate_backend(api)
        assert errors == [], f"DemoAPI missing: {errors}"

    def test_empty_object_fails(self):
        errors = validate_backend(object())
        assert len(errors) >= 4

    def test_partial_api_reports_missing(self):
        class Partial:
            class users:
                @staticmethod
                def get(uid):
                    pass

            class groups:
                pass

        errors = validate_backend(Partial())
        assert any("queues" in e for e in errors)
        assert any("routing" in e for e in errors)
