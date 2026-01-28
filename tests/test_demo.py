"""Tests for core.demo — DemoAPI operations."""

from core.demo import DemoAPI


class TestDemoUsers:
    def setup_method(self):
        self.api = DemoAPI()

    def test_list_page(self):
        resp = self.api.users.list_page(page_size=10, page_number=1)
        assert resp.success
        assert len(resp.data["entities"]) == 10

    def test_search(self):
        results = self.api.users.search("alice")
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_search_by_email(self):
        user = self.api.users.search_by_email("alice.johnson@acmecorp.com")
        assert user is not None
        assert user["name"] == "Alice Johnson"

    def test_search_by_email_not_found(self):
        user = self.api.users.search_by_email("nobody@example.com")
        assert user is None

    def test_get_user(self):
        resp = self.api.users.get("user-0000")
        assert resp.success
        assert resp.data["name"] == "Alice Johnson"

    def test_get_user_not_found(self):
        resp = self.api.users.get("nonexistent")
        assert not resp.success


class TestDemoGroups:
    def setup_method(self):
        self.api = DemoAPI()

    def test_list_page(self):
        resp = self.api.groups.list_page(page_size=25, page_number=1)
        assert resp.success
        assert len(resp.data["entities"]) > 0

    def test_search(self):
        results = self.api.groups.search("support")
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_get_members(self):
        members = self.api.groups.get_members("group-001")
        assert isinstance(members, list)


class TestDemoQueues:
    def setup_method(self):
        self.api = DemoAPI()

    def test_list_page(self):
        resp = self.api.queues.list_page(page_size=25, page_number=1)
        assert resp.success
        assert len(resp.data["entities"]) > 0

    def test_search(self):
        results = self.api.queues.search("support")
        assert isinstance(results, list)


class TestDemoRouting:
    def setup_method(self):
        self.api = DemoAPI()

    def test_get_skills(self):
        skills = self.api.routing.get_skills()
        assert isinstance(skills, list)
        assert len(skills) > 0

    def test_list_skills_page(self):
        resp = self.api.routing.list_skills_page(page_size=10, page_number=1)
        assert resp.success
        assert len(resp.data["entities"]) > 0
