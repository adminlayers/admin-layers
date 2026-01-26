"""
Genesys Cloud API client.
"""

import requests
from typing import Optional, List, Dict, Any, Generator
from dataclasses import dataclass

from .auth import GenesysAuth


@dataclass
class APIResponse:
    """Standardized API response."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    status_code: Optional[int] = None


class GenesysCloudAPI:
    """
    Genesys Cloud API client.

    Provides methods for common API operations with automatic
    pagination, error handling, and token refresh.

    Usage:
        auth = GenesysAuth.from_config()
        auth.authenticate()
        api = GenesysCloudAPI(auth)

        # Get users
        users = api.users.search_by_email("user@example.com")

        # Get groups
        groups = api.groups.search("Support")
    """

    def __init__(self, auth: GenesysAuth):
        """
        Initialize API client.

        Args:
            auth: Authenticated GenesysAuth instance
        """
        self.auth = auth
        self._base_url = auth.config.api_url

        # Initialize sub-APIs
        self.users = UsersAPI(self)
        self.groups = GroupsAPI(self)
        self.queues = QueuesAPI(self)
        self.conversations = ConversationsAPI(self)
        self.routing = RoutingAPI(self)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        timeout: int = 30
    ) -> APIResponse:
        """
        Make authenticated API request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint (e.g., /api/v2/users)
            params: Query parameters
            json: JSON body
            timeout: Request timeout in seconds

        Returns:
            APIResponse with result
        """
        # Ensure authenticated
        if not self.auth.refresh_if_needed():
            return APIResponse(success=False, error="Authentication failed")

        url = f"{self._base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.auth.get_headers(),
                params=params,
                json=json,
                timeout=timeout
            )

            if response.status_code == 204:
                return APIResponse(success=True, data=None, status_code=204)

            response.raise_for_status()

            return APIResponse(
                success=True,
                data=response.json() if response.text else None,
                status_code=response.status_code
            )

        except requests.exceptions.Timeout:
            return APIResponse(success=False, error="Request timed out", status_code=None)
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            status_code = None
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', error_data.get('error', str(e)))
                except:
                    error_msg = e.response.text[:500] if e.response.text else str(e)
            return APIResponse(success=False, error=error_msg, status_code=status_code)

    def get(self, endpoint: str, params: Optional[Dict] = None) -> APIResponse:
        """GET request."""
        return self._request('GET', endpoint, params=params)

    def post(self, endpoint: str, json: Optional[Dict] = None, params: Optional[Dict] = None) -> APIResponse:
        """POST request."""
        return self._request('POST', endpoint, json=json, params=params)

    def put(self, endpoint: str, json: Optional[Dict] = None) -> APIResponse:
        """PUT request."""
        return self._request('PUT', endpoint, json=json)

    def patch(self, endpoint: str, json: Optional[Dict] = None) -> APIResponse:
        """PATCH request."""
        return self._request('PATCH', endpoint, json=json)

    def delete(self, endpoint: str, params: Optional[Dict] = None) -> APIResponse:
        """DELETE request."""
        return self._request('DELETE', endpoint, params=params)

    def paginate(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        page_size: int = 100,
        max_pages: Optional[int] = None
    ) -> Generator[Dict, None, None]:
        """
        Paginate through API results.

        Args:
            endpoint: API endpoint
            params: Additional query parameters
            page_size: Results per page
            max_pages: Maximum pages to fetch (None for all)

        Yields:
            Individual entities from paginated results
        """
        params = params or {}
        params['pageSize'] = page_size
        page = 1

        while True:
            params['pageNumber'] = page
            response = self.get(endpoint, params)

            if not response.success:
                break

            data = response.data or {}
            entities = data.get('entities', [])

            for entity in entities:
                yield entity

            page_count = data.get('pageCount', 1)

            if page >= page_count:
                break

            if max_pages and page >= max_pages:
                break

            page += 1


class UsersAPI:
    """Users API operations."""

    def __init__(self, client: GenesysCloudAPI):
        self._client = client

    def get(self, user_id: str) -> APIResponse:
        """Get user by ID."""
        return self._client.get(f'/api/v2/users/{user_id}')

    def search(self, query: str, fields: List[str] = None) -> List[Dict]:
        """
        Search for users.

        Args:
            query: Search query
            fields: Fields to search (default: all)

        Returns:
            List of matching users
        """
        body = {
            "query": [{
                "type": "QUERY_STRING",
                "value": query
            }]
        }

        if fields:
            body["query"][0]["fields"] = fields

        response = self._client.post('/api/v2/users/search', json=body)
        return response.data.get('results', []) if response.success else []

    def search_by_email(self, email: str) -> Optional[Dict]:
        """
        Find user by exact email.

        Args:
            email: Email address

        Returns:
            User dict or None
        """
        body = {
            "query": [{
                "type": "EXACT",
                "fields": ["email"],
                "value": email
            }]
        }

        response = self._client.post('/api/v2/users/search', json=body)
        if response.success:
            results = response.data.get('results', [])
            return results[0] if results else None
        return None

    def get_queues(self, user_id: str) -> List[Dict]:
        """Get queues a user belongs to."""
        return list(self._client.paginate(f'/api/v2/users/{user_id}/queues'))

    def get_groups(self, user_id: str) -> APIResponse:
        """Get groups a user belongs to."""
        return self._client.get(f'/api/v2/users/{user_id}/groups')

    def list(self, page_size: int = 100, max_pages: int = None) -> Generator[Dict, None, None]:
        """
        List all users.

        Args:
            page_size: Results per page
            max_pages: Maximum pages to fetch

        Yields:
            User dicts
        """
        yield from self._client.paginate('/api/v2/users', page_size=page_size, max_pages=max_pages)


class GroupsAPI:
    """Groups API operations."""

    def __init__(self, client: GenesysCloudAPI):
        self._client = client

    def get(self, group_id: str) -> APIResponse:
        """Get group by ID."""
        return self._client.get(f'/api/v2/groups/{group_id}')

    def search(self, query: str) -> List[Dict]:
        """
        Search for groups by name.

        Args:
            query: Search query

        Returns:
            List of matching groups
        """
        body = {
            "pageSize": 100,
            "query": [{
                "type": "CONTAINS",
                "fields": ["name"],
                "value": query
            }]
        }

        response = self._client.post('/api/v2/groups/search', json=body)
        return response.data.get('results', []) if response.success else []

    def get_members(self, group_id: str) -> List[Dict]:
        """
        Get all members of a group.

        Args:
            group_id: Group ID

        Returns:
            List of member user dicts
        """
        return list(self._client.paginate(f'/api/v2/groups/{group_id}/members'))

    def add_members(self, group_id: str, member_ids: List[str]) -> APIResponse:
        """
        Add members to a group.

        Args:
            group_id: Group ID
            member_ids: List of user IDs to add

        Returns:
            APIResponse
        """
        body = {
            "memberIds": member_ids,
            "version": 1
        }
        return self._client.post(f'/api/v2/groups/{group_id}/members', json=body)

    def remove_members(self, group_id: str, member_ids: List[str]) -> APIResponse:
        """
        Remove members from a group.

        Args:
            group_id: Group ID
            member_ids: List of user IDs to remove

        Returns:
            APIResponse
        """
        ids_param = ",".join(member_ids)
        return self._client.delete(f'/api/v2/groups/{group_id}/members', params={'ids': ids_param})

    def list(self, page_size: int = 100) -> Generator[Dict, None, None]:
        """List all groups."""
        yield from self._client.paginate('/api/v2/groups', page_size=page_size)


class QueuesAPI:
    """Queues API operations."""

    def __init__(self, client: GenesysCloudAPI):
        self._client = client

    def get(self, queue_id: str) -> APIResponse:
        """Get queue by ID."""
        return self._client.get(f'/api/v2/routing/queues/{queue_id}')

    def search(self, query: str) -> List[Dict]:
        """Search queues by name."""
        body = {
            "pageSize": 100,
            "query": [{
                "type": "CONTAINS",
                "fields": ["name"],
                "value": query
            }]
        }
        response = self._client.post('/api/v2/routing/queues/search', json=body)
        return response.data.get('results', []) if response.success else []

    def get_members(self, queue_id: str) -> List[Dict]:
        """Get queue members."""
        return list(self._client.paginate(f'/api/v2/routing/queues/{queue_id}/members'))

    def add_members(self, queue_id: str, member_ids: List[str]) -> APIResponse:
        """Add members to a queue."""
        body = [{"id": uid, "joined": True} for uid in member_ids]
        return self._client.post(f'/api/v2/routing/queues/{queue_id}/members', json=body)

    def remove_members(self, queue_id: str, member_ids: List[str]) -> APIResponse:
        """Remove members from a queue."""
        body = [{"id": uid, "joined": False} for uid in member_ids]
        return self._client.post(f'/api/v2/routing/queues/{queue_id}/members', json=body)

    def list(self, page_size: int = 100) -> Generator[Dict, None, None]:
        """List all queues."""
        yield from self._client.paginate('/api/v2/routing/queues', page_size=page_size)


class ConversationsAPI:
    """Conversations API operations."""

    def __init__(self, client: GenesysCloudAPI):
        self._client = client

    def get(self, conversation_id: str) -> APIResponse:
        """Get conversation by ID."""
        return self._client.get(f'/api/v2/conversations/{conversation_id}')

    def get_details(self, conversation_id: str) -> APIResponse:
        """Get conversation analytics details."""
        return self._client.get(f'/api/v2/analytics/conversations/{conversation_id}/details')

    def disconnect(self, conversation_id: str) -> APIResponse:
        """Disconnect a conversation."""
        return self._client.post(f'/api/v2/conversations/{conversation_id}/disconnect')

    def query(
        self,
        interval: str,
        filters: List[Dict] = None,
        page_size: int = 100
    ) -> List[Dict]:
        """
        Query conversation analytics.

        Args:
            interval: ISO 8601 interval (e.g., "2024-01-01T00:00:00Z/2024-01-02T00:00:00Z")
            filters: Segment filters
            page_size: Results per page

        Returns:
            List of conversations
        """
        body = {
            "interval": interval,
            "paging": {"pageSize": page_size, "pageNumber": 1}
        }

        if filters:
            body["segmentFilters"] = filters

        response = self._client.post('/api/v2/analytics/conversations/details/query', json=body)
        return response.data.get('conversations', []) if response.success else []


class RoutingAPI:
    """Routing API operations."""

    def __init__(self, client: GenesysCloudAPI):
        self._client = client

    def get_skills(self) -> List[Dict]:
        """Get all routing skills."""
        return list(self._client.paginate('/api/v2/routing/skills'))

    def get_languages(self) -> List[Dict]:
        """Get all routing languages."""
        return list(self._client.paginate('/api/v2/routing/languages'))

    def get_wrapup_codes(self) -> List[Dict]:
        """Get all wrapup codes."""
        return list(self._client.paginate('/api/v2/routing/wrapupcodes'))

    def get_user_skills(self, user_id: str) -> List[Dict]:
        """Get user's routing skills."""
        return list(self._client.paginate(f'/api/v2/users/{user_id}/routingskills'))

    def add_user_skill(self, user_id: str, skill_id: str, proficiency: float = 1.0) -> APIResponse:
        """Add skill to user."""
        body = {
            "id": skill_id,
            "proficiency": proficiency
        }
        return self._client.post(f'/api/v2/users/{user_id}/routingskills', json=body)

    def remove_user_skill(self, user_id: str, skill_id: str) -> APIResponse:
        """Remove skill from user."""
        return self._client.delete(f'/api/v2/users/{user_id}/routingskills/{skill_id}')
