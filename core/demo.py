"""
Demo Mode Module
Provides mock data and API simulation for running Admin Layers
without real Genesys Cloud credentials.

Enables hosted demo deployments where visitors can explore the UI
without connecting to a real org.
"""

import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional


# =============================================================================
# Demo Data
# =============================================================================

DEMO_USERS = [
    {"id": f"user-{i:04d}", "name": name, "email": f"{name.lower().replace(' ', '.')}@acmecorp.com",
     "department": dept, "title": title, "state": "active"}
    for i, (name, dept, title) in enumerate([
        ("Alice Johnson", "Support", "Senior Agent"),
        ("Bob Martinez", "Support", "Team Lead"),
        ("Carol Williams", "Sales", "Account Executive"),
        ("David Chen", "Support", "Agent"),
        ("Emma Davis", "Engineering", "Developer"),
        ("Frank Wilson", "Support", "Senior Agent"),
        ("Grace Lee", "Sales", "Sales Manager"),
        ("Henry Brown", "Support", "Agent"),
        ("Iris Taylor", "QA", "Quality Analyst"),
        ("James Anderson", "Support", "Agent"),
        ("Karen Thomas", "Support", "Supervisor"),
        ("Liam Jackson", "Sales", "SDR"),
        ("Maria Garcia", "Support", "Agent"),
        ("Nathan White", "Engineering", "DevOps Engineer"),
        ("Olivia Harris", "Support", "Senior Agent"),
        ("Patrick Martin", "Support", "Agent"),
        ("Quinn Robinson", "Sales", "Account Manager"),
        ("Rachel Clark", "Support", "Agent"),
        ("Samuel Lewis", "QA", "QA Lead"),
        ("Tina Walker", "Support", "Agent"),
        ("Ulysses Hall", "Support", "Agent"),
        ("Victoria Allen", "Sales", "VP Sales"),
        ("William Young", "Engineering", "CTO"),
        ("Xena King", "Support", "Agent"),
        ("Yuki Wright", "Support", "Trainer"),
        ("Zachary Scott", "Support", "Agent"),
        ("Angela Adams", "HR", "HR Manager"),
        ("Brandon Baker", "Support", "Agent"),
        ("Catherine Nelson", "Support", "Senior Agent"),
        ("Derek Hill", "Support", "Agent"),
    ])
]

DEMO_GROUPS = [
    {"id": "grp-0001", "name": "Tier 1 Support", "description": "Front-line support agents",
     "memberCount": 15, "state": "active", "type": "official",
     "visibility": "public", "rulesVisible": True},
    {"id": "grp-0002", "name": "Tier 2 Support", "description": "Escalation support team",
     "memberCount": 8, "state": "active", "type": "official",
     "visibility": "public", "rulesVisible": True},
    {"id": "grp-0003", "name": "Sales Team", "description": "All sales representatives",
     "memberCount": 6, "state": "active", "type": "official",
     "visibility": "public", "rulesVisible": True},
    {"id": "grp-0004", "name": "All Hands", "description": "All employees",
     "memberCount": 30, "state": "active", "type": "official",
     "visibility": "public", "rulesVisible": True},
    {"id": "grp-0005", "name": "Weekend Coverage", "description": "Weekend shift agents",
     "memberCount": 10, "state": "active", "type": "official",
     "visibility": "members", "rulesVisible": True},
]

DEMO_QUEUES = [
    {"id": "queue-0001", "name": "General Support", "description": "General inbound support",
     "memberCount": 12, "mediaSettings": {"call": {"alertingTimeoutSeconds": 30}},
     "acwSettings": {"wrapupPrompt": "MANDATORY", "timeoutMs": 60000},
     "skillEvaluationMethod": "BEST", "callingPartyName": "Acme Support",
     "callingPartyNumber": "+18005551234"},
    {"id": "queue-0002", "name": "Billing Support", "description": "Billing and payments",
     "memberCount": 8, "mediaSettings": {"call": {"alertingTimeoutSeconds": 25}},
     "acwSettings": {"wrapupPrompt": "MANDATORY", "timeoutMs": 45000},
     "skillEvaluationMethod": "BEST", "callingPartyName": "Acme Billing",
     "callingPartyNumber": "+18005555678"},
    {"id": "queue-0003", "name": "Sales Inbound", "description": "Inbound sales calls",
     "memberCount": 6, "mediaSettings": {"call": {"alertingTimeoutSeconds": 20}},
     "acwSettings": {"wrapupPrompt": "OPTIONAL", "timeoutMs": 30000},
     "skillEvaluationMethod": "ALL", "callingPartyName": "Acme Sales",
     "callingPartyNumber": "+18005559012"},
    {"id": "queue-0004", "name": "Technical Support", "description": "Technical troubleshooting",
     "memberCount": 5, "mediaSettings": {"call": {"alertingTimeoutSeconds": 35}},
     "acwSettings": {"wrapupPrompt": "MANDATORY", "timeoutMs": 90000},
     "skillEvaluationMethod": "BEST", "callingPartyName": "Acme Tech",
     "callingPartyNumber": "+18005553456"},
    {"id": "queue-0005", "name": "VIP Support", "description": "High-priority customer support",
     "memberCount": 4, "mediaSettings": {"call": {"alertingTimeoutSeconds": 15}},
     "acwSettings": {"wrapupPrompt": "MANDATORY", "timeoutMs": 120000},
     "skillEvaluationMethod": "BEST", "callingPartyName": "Acme VIP",
     "callingPartyNumber": "+18005557890"},
]

DEMO_SKILLS = [
    {"id": "skill-0001", "name": "English", "state": "active"},
    {"id": "skill-0002", "name": "Spanish", "state": "active"},
    {"id": "skill-0003", "name": "French", "state": "active"},
    {"id": "skill-0004", "name": "Billing", "state": "active"},
    {"id": "skill-0005", "name": "Technical Support", "state": "active"},
    {"id": "skill-0006", "name": "Salesforce", "state": "active"},
    {"id": "skill-0007", "name": "Escalation Handling", "state": "active"},
    {"id": "skill-0008", "name": "Chat Support", "state": "active"},
    {"id": "skill-0009", "name": "Email Support", "state": "active"},
    {"id": "skill-0010", "name": "Product Knowledge", "state": "active"},
    {"id": "skill-0011", "name": "Returns & Refunds", "state": "active"},
    {"id": "skill-0012", "name": "Account Management", "state": "active"},
]

# User-skill assignments (user_id -> list of skill assignments)
DEMO_USER_SKILLS = {}
for user in DEMO_USERS:
    n_skills = random.Random(user["id"]).randint(1, 5)
    skills = random.Random(user["id"]).sample(DEMO_SKILLS, min(n_skills, len(DEMO_SKILLS)))
    DEMO_USER_SKILLS[user["id"]] = [
        {"id": s["id"], "name": s["name"], "state": "active",
         "proficiency": round(random.Random(user["id"] + s["id"]).uniform(1.0, 5.0), 1)}
        for s in skills
    ]

# Group membership mappings
DEMO_GROUP_MEMBERS = {
    "grp-0001": DEMO_USERS[:15],
    "grp-0002": DEMO_USERS[0:8],
    "grp-0003": [u for u in DEMO_USERS if u["department"] == "Sales"],
    "grp-0004": DEMO_USERS,
    "grp-0005": DEMO_USERS[:10],
}

# Queue membership mappings
DEMO_QUEUE_MEMBERS = {
    "queue-0001": DEMO_USERS[:12],
    "queue-0002": DEMO_USERS[0:8],
    "queue-0003": [u for u in DEMO_USERS if u["department"] == "Sales"],
    "queue-0004": DEMO_USERS[3:8],
    "queue-0005": DEMO_USERS[:4],
}

DEMO_DATA = {
    "users": DEMO_USERS,
    "groups": DEMO_GROUPS,
    "queues": DEMO_QUEUES,
    "skills": DEMO_SKILLS,
    "user_skills": DEMO_USER_SKILLS,
    "group_members": DEMO_GROUP_MEMBERS,
    "queue_members": DEMO_QUEUE_MEMBERS,
}


# =============================================================================
# Demo Mode State (framework-agnostic)
# =============================================================================

_demo_mode: bool = False


def is_demo_mode() -> bool:
    """Check if demo mode is active."""
    return _demo_mode


def set_demo_mode(enabled: bool) -> None:
    """Enable or disable demo mode."""
    global _demo_mode
    _demo_mode = enabled


# =============================================================================
# Mock API Response
# =============================================================================

@dataclass
class MockAPIResponse:
    """Mock API response matching APIResponse interface."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    status_code: Optional[int] = None


# =============================================================================
# Demo API Client
# =============================================================================

class DemoUsersAPI:
    """Mock Users API."""

    def get(self, user_id: str) -> MockAPIResponse:
        for u in DEMO_USERS:
            if u["id"] == user_id:
                return MockAPIResponse(success=True, data=u, status_code=200)
        return MockAPIResponse(success=False, error="User not found", status_code=404)

    def search(self, query: str, fields: List[str] = None) -> List[Dict]:
        query_lower = query.lower()
        return [u for u in DEMO_USERS
                if query_lower in u["name"].lower() or query_lower in u["email"].lower()]

    def search_by_email(self, email: str) -> Optional[Dict]:
        email_lower = email.lower()
        for u in DEMO_USERS:
            if u["email"].lower() == email_lower:
                return u
        return None

    def get_queues(self, user_id: str) -> List[Dict]:
        result = []
        for qid, members in DEMO_QUEUE_MEMBERS.items():
            if any(m["id"] == user_id for m in members):
                for q in DEMO_QUEUES:
                    if q["id"] == qid:
                        result.append(q)
        return result

    def get_groups(self, user_id: str) -> MockAPIResponse:
        result = []
        for gid, members in DEMO_GROUP_MEMBERS.items():
            if any(m["id"] == user_id for m in members):
                for g in DEMO_GROUPS:
                    if g["id"] == gid:
                        result.append(g)
        return MockAPIResponse(success=True, data={"entities": result}, status_code=200)

    def list(self, page_size: int = 100, max_pages: int = None) -> Generator[Dict, None, None]:
        for u in DEMO_USERS:
            yield u

    def list_page(self, page_size: int = 25, page_number: int = 1) -> MockAPIResponse:
        start = (page_number - 1) * page_size
        end = start + page_size
        entities = DEMO_USERS[start:end]
        total = len(DEMO_USERS)
        page_count = max(1, (total + page_size - 1) // page_size)
        return MockAPIResponse(
            success=True,
            data={
                "entities": entities,
                "pageNumber": page_number,
                "pageSize": page_size,
                "pageCount": page_count,
                "total": total,
            },
            status_code=200,
        )

    def update(self, user_id: str, data: Dict[str, Any]) -> MockAPIResponse:
        for user in DEMO_USERS:
            if user["id"] == user_id:
                user.update(data)
                return MockAPIResponse(success=True, data=user, status_code=200)
        return MockAPIResponse(success=False, error="User not found", status_code=404)


class DemoGroupsAPI:
    """Mock Groups API."""

    def get(self, group_id: str) -> MockAPIResponse:
        for g in DEMO_GROUPS:
            if g["id"] == group_id:
                return MockAPIResponse(success=True, data=g, status_code=200)
        return MockAPIResponse(success=False, error="Group not found", status_code=404)

    def search(self, query: str) -> List[Dict]:
        query_lower = query.lower()
        return [g for g in DEMO_GROUPS if query_lower in g["name"].lower()]

    def get_members(self, group_id: str) -> List[Dict]:
        return DEMO_GROUP_MEMBERS.get(group_id, [])

    def add_members(self, group_id: str, member_ids: List[str]) -> MockAPIResponse:
        members = DEMO_GROUP_MEMBERS.setdefault(group_id, [])
        existing_ids = {m["id"] for m in members}
        for uid in member_ids:
            if uid not in existing_ids:
                user = next((u for u in DEMO_USERS if u["id"] == uid), None)
                if user:
                    members.append(user)
        return MockAPIResponse(success=True, data={"added": len(member_ids)}, status_code=200)

    def remove_members(self, group_id: str, member_ids: List[str]) -> MockAPIResponse:
        members = DEMO_GROUP_MEMBERS.get(group_id, [])
        DEMO_GROUP_MEMBERS[group_id] = [m for m in members if m["id"] not in member_ids]
        return MockAPIResponse(success=True, data=None, status_code=204)

    def list(self, page_size: int = 100) -> Generator[Dict, None, None]:
        for g in DEMO_GROUPS:
            yield g

    def list_page(self, page_size: int = 25, page_number: int = 1) -> MockAPIResponse:
        start = (page_number - 1) * page_size
        end = start + page_size
        entities = DEMO_GROUPS[start:end]
        total = len(DEMO_GROUPS)
        page_count = max(1, (total + page_size - 1) // page_size)
        return MockAPIResponse(
            success=True,
            data={
                "entities": entities,
                "pageNumber": page_number,
                "pageSize": page_size,
                "pageCount": page_count,
                "total": total,
            },
            status_code=200,
        )

    def create(self, name: str, description: str, group_type: str, visibility: str) -> MockAPIResponse:
        group_id = f"grp-{uuid.uuid4().hex[:6]}"
        group = {
            "id": group_id,
            "name": name,
            "description": description,
            "memberCount": 0,
            "state": "active",
            "type": group_type,
            "visibility": visibility,
            "rulesVisible": True,
        }
        DEMO_GROUPS.append(group)
        DEMO_GROUP_MEMBERS[group_id] = []
        return MockAPIResponse(success=True, data=group, status_code=200)

    def update(self, group_id: str, data: Dict[str, Any]) -> MockAPIResponse:
        for group in DEMO_GROUPS:
            if group["id"] == group_id:
                group.update(data)
                return MockAPIResponse(success=True, data=group, status_code=200)
        return MockAPIResponse(success=False, error="Group not found", status_code=404)

    def delete(self, group_id: str) -> MockAPIResponse:
        for idx, group in enumerate(DEMO_GROUPS):
            if group["id"] == group_id:
                DEMO_GROUPS.pop(idx)
                DEMO_GROUP_MEMBERS.pop(group_id, None)
                return MockAPIResponse(success=True, data=None, status_code=204)
        return MockAPIResponse(success=False, error="Group not found", status_code=404)


class DemoQueuesAPI:
    """Mock Queues API."""

    def get(self, queue_id: str) -> MockAPIResponse:
        for q in DEMO_QUEUES:
            if q["id"] == queue_id:
                return MockAPIResponse(success=True, data=q, status_code=200)
        return MockAPIResponse(success=False, error="Queue not found", status_code=404)

    def search(self, query: str) -> List[Dict]:
        query_lower = query.lower()
        return [q for q in DEMO_QUEUES if query_lower in q["name"].lower()]

    def get_members(self, queue_id: str) -> List[Dict]:
        return DEMO_QUEUE_MEMBERS.get(queue_id, [])

    def add_members(self, queue_id: str, member_ids: List[str]) -> MockAPIResponse:
        members = DEMO_QUEUE_MEMBERS.setdefault(queue_id, [])
        existing_ids = {m["id"] for m in members}
        for uid in member_ids:
            if uid not in existing_ids:
                user = next((u for u in DEMO_USERS if u["id"] == uid), None)
                if user:
                    members.append(user)
        return MockAPIResponse(success=True, data={"added": len(member_ids)}, status_code=200)

    def remove_members(self, queue_id: str, member_ids: List[str]) -> MockAPIResponse:
        members = DEMO_QUEUE_MEMBERS.get(queue_id, [])
        DEMO_QUEUE_MEMBERS[queue_id] = [m for m in members if m["id"] not in member_ids]
        return MockAPIResponse(success=True, data=None, status_code=200)

    def list(self, page_size: int = 100, max_pages: int = None) -> Generator[Dict, None, None]:
        for q in DEMO_QUEUES:
            yield q

    def list_page(self, page_size: int = 25, page_number: int = 1) -> MockAPIResponse:
        start = (page_number - 1) * page_size
        end = start + page_size
        entities = DEMO_QUEUES[start:end]
        total = len(DEMO_QUEUES)
        page_count = max(1, (total + page_size - 1) // page_size)
        return MockAPIResponse(
            success=True,
            data={
                "entities": entities,
                "pageNumber": page_number,
                "pageSize": page_size,
                "pageCount": page_count,
                "total": total,
            },
            status_code=200,
        )

    def create(self, data: Dict[str, Any]) -> MockAPIResponse:
        queue_id = f"queue-{uuid.uuid4().hex[:6]}"
        queue = {
            "id": queue_id,
            "memberCount": 0,
            "mediaSettings": data.get("mediaSettings", {"call": {"alertingTimeoutSeconds": 30}}),
            "acwSettings": data.get("acwSettings", {"wrapupPrompt": "MANDATORY", "timeoutMs": 60000}),
            "skillEvaluationMethod": data.get("skillEvaluationMethod", "BEST"),
            "callingPartyName": data.get("callingPartyName", ""),
            "callingPartyNumber": data.get("callingPartyNumber", ""),
            "name": data.get("name", "New Queue"),
            "description": data.get("description", ""),
        }
        DEMO_QUEUES.append(queue)
        DEMO_QUEUE_MEMBERS[queue_id] = []
        return MockAPIResponse(success=True, data=queue, status_code=200)

    def update(self, queue_id: str, data: Dict[str, Any]) -> MockAPIResponse:
        for queue in DEMO_QUEUES:
            if queue["id"] == queue_id:
                queue.update(data)
                return MockAPIResponse(success=True, data=queue, status_code=200)
        return MockAPIResponse(success=False, error="Queue not found", status_code=404)

    def delete(self, queue_id: str) -> MockAPIResponse:
        for idx, queue in enumerate(DEMO_QUEUES):
            if queue["id"] == queue_id:
                DEMO_QUEUES.pop(idx)
                DEMO_QUEUE_MEMBERS.pop(queue_id, None)
                return MockAPIResponse(success=True, data=None, status_code=204)
        return MockAPIResponse(success=False, error="Queue not found", status_code=404)


class DemoRoutingAPI:
    """Mock Routing API."""

    def get_skills(self) -> List[Dict]:
        return DEMO_SKILLS

    def get_skill(self, skill_id: str) -> MockAPIResponse:
        for skill in DEMO_SKILLS:
            if skill["id"] == skill_id:
                return MockAPIResponse(success=True, data=skill, status_code=200)
        return MockAPIResponse(success=False, error="Skill not found", status_code=404)

    def list_skills_page(self, page_size: int = 25, page_number: int = 1) -> MockAPIResponse:
        start = (page_number - 1) * page_size
        end = start + page_size
        entities = DEMO_SKILLS[start:end]
        total = len(DEMO_SKILLS)
        page_count = max(1, (total + page_size - 1) // page_size)
        return MockAPIResponse(
            success=True,
            data={
                "entities": entities,
                "pageNumber": page_number,
                "pageSize": page_size,
                "pageCount": page_count,
                "total": total,
            },
            status_code=200,
        )

    def get_languages(self) -> List[Dict]:
        return [{"id": "lang-001", "name": "English", "state": "active"},
                {"id": "lang-002", "name": "Spanish", "state": "active"}]

    def get_wrapup_codes(self) -> List[Dict]:
        return [{"id": "wc-001", "name": "Resolved", "state": "active"},
                {"id": "wc-002", "name": "Follow-up Required", "state": "active"},
                {"id": "wc-003", "name": "Escalated", "state": "active"}]

    def get_user_skills(self, user_id: str) -> List[Dict]:
        return DEMO_USER_SKILLS.get(user_id, [])

    def add_user_skill(self, user_id: str, skill_id: str, proficiency: float = 1.0) -> MockAPIResponse:
        assignments = DEMO_USER_SKILLS.setdefault(user_id, [])
        skill = next((s for s in DEMO_SKILLS if s["id"] == skill_id), None)
        if skill:
            if not any(s["id"] == skill_id for s in assignments):
                assignments.append({
                    "id": skill_id,
                    "name": skill["name"],
                    "state": skill.get("state", "active"),
                    "proficiency": proficiency,
                })
        return MockAPIResponse(success=True, data={"id": skill_id}, status_code=200)

    def remove_user_skill(self, user_id: str, skill_id: str) -> MockAPIResponse:
        assignments = DEMO_USER_SKILLS.get(user_id, [])
        DEMO_USER_SKILLS[user_id] = [s for s in assignments if s.get("id") != skill_id]
        return MockAPIResponse(success=True, data=None, status_code=204)

    def create_skill(self, name: str, description: str, state: str) -> MockAPIResponse:
        skill_id = f"skill-{uuid.uuid4().hex[:6]}"
        skill = {"id": skill_id, "name": name, "description": description, "state": state}
        DEMO_SKILLS.append(skill)
        return MockAPIResponse(success=True, data=skill, status_code=200)

    def update_skill(self, skill_id: str, data: Dict[str, Any]) -> MockAPIResponse:
        for skill in DEMO_SKILLS:
            if skill["id"] == skill_id:
                skill.update(data)
                return MockAPIResponse(success=True, data=skill, status_code=200)
        return MockAPIResponse(success=False, error="Skill not found", status_code=404)

    def delete_skill(self, skill_id: str) -> MockAPIResponse:
        for idx, skill in enumerate(DEMO_SKILLS):
            if skill["id"] == skill_id:
                DEMO_SKILLS.pop(idx)
                return MockAPIResponse(success=True, data=None, status_code=204)
        return MockAPIResponse(success=False, error="Skill not found", status_code=404)


class DemoConversationsAPI:
    """Mock Conversations API."""

    def get(self, conversation_id: str) -> MockAPIResponse:
        return MockAPIResponse(success=False, error="Not available in demo mode", status_code=501)

    def get_details(self, conversation_id: str) -> MockAPIResponse:
        return MockAPIResponse(success=False, error="Not available in demo mode", status_code=501)

    def disconnect(self, conversation_id: str) -> MockAPIResponse:
        return MockAPIResponse(success=False, error="Not available in demo mode", status_code=501)

    def query(self, interval: str, filters=None, page_size=100) -> List[Dict]:
        return []


class DemoAPI:
    """
    Mock Genesys Cloud API client for demo mode.
    Implements the same interface as GenesysCloudAPI using mock data.
    """

    def __init__(self):
        self.users = DemoUsersAPI()
        self.groups = DemoGroupsAPI()
        self.queues = DemoQueuesAPI()
        self.routing = DemoRoutingAPI()
        self.conversations = DemoConversationsAPI()
