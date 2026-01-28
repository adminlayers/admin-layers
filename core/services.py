"""
Service Layer
Defines the backend interface (Protocol classes) that all backends must implement.
This makes the backend extensible and easily swappable between:
  - Live Genesys Cloud API
  - Demo mode (in-memory mock data)
  - Future: local database, file-based, etc.

Each resource type has a standard set of endpoints:
  - list_page: paginated listing
  - get: single resource by ID
  - search: text search
  - create / update / delete: CRUD
  - get_members / add_members / remove_members: membership ops
"""

from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional, Protocol, runtime_checkable


# =============================================================================
# Response type
# =============================================================================

@dataclass
class ServiceResponse:
    """Standard response from any backend operation."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    status_code: Optional[int] = None


# =============================================================================
# Resource endpoint protocols
# =============================================================================

@runtime_checkable
class UsersEndpoint(Protocol):
    """Standard operations for the Users resource."""

    def get(self, user_id: str) -> ServiceResponse:
        """Get user by ID."""
        ...

    def search(self, query: str, fields: List[str] = None) -> List[Dict]:
        """Search users by name/email."""
        ...

    def search_by_email(self, email: str) -> Optional[Dict]:
        """Find a single user by exact email match."""
        ...

    def list(self, page_size: int = 100, max_pages: int = None) -> Generator[Dict, None, None]:
        """Iterate all users."""
        ...

    def list_page(self, page_size: int = 25, page_number: int = 1) -> ServiceResponse:
        """Get a single page of users."""
        ...

    def update(self, user_id: str, data: Dict[str, Any]) -> ServiceResponse:
        """Update user fields."""
        ...

    def get_queues(self, user_id: str) -> List[Dict]:
        """Get queues a user belongs to."""
        ...

    def get_groups(self, user_id: str) -> ServiceResponse:
        """Get groups a user belongs to."""
        ...


@runtime_checkable
class GroupsEndpoint(Protocol):
    """Standard operations for the Groups resource."""

    def get(self, group_id: str) -> ServiceResponse:
        """Get group by ID."""
        ...

    def search(self, query: str) -> List[Dict]:
        """Search groups by name."""
        ...

    def list(self, page_size: int = 100) -> Generator[Dict, None, None]:
        """Iterate all groups."""
        ...

    def list_page(self, page_size: int = 25, page_number: int = 1) -> ServiceResponse:
        """Get a single page of groups."""
        ...

    def create(self, name: str, description: str, group_type: str, visibility: str) -> ServiceResponse:
        """Create a new group."""
        ...

    def update(self, group_id: str, data: Dict[str, Any]) -> ServiceResponse:
        """Update group fields."""
        ...

    def delete(self, group_id: str) -> ServiceResponse:
        """Delete a group."""
        ...

    def get_members(self, group_id: str) -> List[Dict]:
        """Get all members of a group."""
        ...

    def add_members(self, group_id: str, member_ids: List[str]) -> ServiceResponse:
        """Add members to a group."""
        ...

    def remove_members(self, group_id: str, member_ids: List[str]) -> ServiceResponse:
        """Remove members from a group."""
        ...


@runtime_checkable
class QueuesEndpoint(Protocol):
    """Standard operations for the Queues resource."""

    def get(self, queue_id: str) -> ServiceResponse:
        """Get queue by ID."""
        ...

    def search(self, query: str) -> List[Dict]:
        """Search queues by name."""
        ...

    def list(self, page_size: int = 100) -> Generator[Dict, None, None]:
        """Iterate all queues."""
        ...

    def list_page(self, page_size: int = 25, page_number: int = 1) -> ServiceResponse:
        """Get a single page of queues."""
        ...

    def create(self, data: Dict[str, Any]) -> ServiceResponse:
        """Create a new queue."""
        ...

    def update(self, queue_id: str, data: Dict[str, Any]) -> ServiceResponse:
        """Update queue fields."""
        ...

    def delete(self, queue_id: str) -> ServiceResponse:
        """Delete a queue."""
        ...

    def get_members(self, queue_id: str) -> List[Dict]:
        """Get all members of a queue."""
        ...

    def add_members(self, queue_id: str, member_ids: List[str]) -> ServiceResponse:
        """Add members to a queue."""
        ...

    def remove_members(self, queue_id: str, member_ids: List[str]) -> ServiceResponse:
        """Remove members from a queue."""
        ...


@runtime_checkable
class RoutingEndpoint(Protocol):
    """Standard operations for Routing (skills, languages, wrapup codes)."""

    def get_skills(self) -> List[Dict]:
        """Get all routing skills."""
        ...

    def get_skill(self, skill_id: str) -> ServiceResponse:
        """Get a single skill by ID."""
        ...

    def list_skills_page(self, page_size: int = 25, page_number: int = 1) -> ServiceResponse:
        """Get a page of skills."""
        ...

    def get_user_skills(self, user_id: str) -> List[Dict]:
        """Get skills assigned to a user."""
        ...

    def add_user_skill(self, user_id: str, skill_id: str, proficiency: float = 1.0) -> ServiceResponse:
        """Assign a skill to a user."""
        ...

    def remove_user_skill(self, user_id: str, skill_id: str) -> ServiceResponse:
        """Remove a skill from a user."""
        ...

    def create_skill(self, name: str, description: str, state: str) -> ServiceResponse:
        """Create a new routing skill."""
        ...

    def update_skill(self, skill_id: str, data: Dict[str, Any]) -> ServiceResponse:
        """Update a routing skill."""
        ...

    def delete_skill(self, skill_id: str) -> ServiceResponse:
        """Delete a routing skill."""
        ...

    def get_languages(self) -> List[Dict]:
        """Get all routing languages."""
        ...

    def get_wrapup_codes(self) -> List[Dict]:
        """Get all wrapup codes."""
        ...


@runtime_checkable
class BackendService(Protocol):
    """
    Top-level backend interface.

    Any backend (live API, demo, database, etc.) must expose these
    resource endpoints. Utilities interact only through this interface,
    making the backend fully swappable.

    Usage in utilities:
        # api is a BackendService — could be live or demo
        resp = self.api.users.list_page(page_size=25, page_number=1)
        members = self.api.groups.get_members(group_id)
    """
    users: UsersEndpoint
    groups: GroupsEndpoint
    queues: QueuesEndpoint
    routing: RoutingEndpoint


def validate_backend(api: Any) -> List[str]:
    """
    Validate that a backend object implements the required interface.
    Returns a list of missing attributes/methods.
    """
    errors = []
    required_attrs = ["users", "groups", "queues", "routing"]
    for attr in required_attrs:
        if not hasattr(api, attr):
            errors.append(f"Missing attribute: {attr}")
            continue

        sub = getattr(api, attr)
        if attr == "users":
            for method in ["get", "search", "search_by_email", "list_page", "update",
                           "get_queues", "get_groups"]:
                if not hasattr(sub, method):
                    errors.append(f"Missing: {attr}.{method}")
        elif attr == "groups":
            for method in ["get", "search", "list_page", "create", "update", "delete",
                           "get_members", "add_members", "remove_members"]:
                if not hasattr(sub, method):
                    errors.append(f"Missing: {attr}.{method}")
        elif attr == "queues":
            for method in ["get", "search", "list_page", "create", "update", "delete",
                           "get_members", "add_members", "remove_members"]:
                if not hasattr(sub, method):
                    errors.append(f"Missing: {attr}.{method}")
        elif attr == "routing":
            for method in ["get_skills", "get_skill", "list_skills_page",
                           "get_user_skills", "add_user_skill", "remove_user_skill",
                           "create_skill", "update_skill", "delete_skill"]:
                if not hasattr(sub, method):
                    errors.append(f"Missing: {attr}.{method}")

    return errors
