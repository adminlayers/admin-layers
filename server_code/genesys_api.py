"""
Anvil Server Module: Genesys Cloud API
Wraps all Genesys Cloud API interactions for server-side execution
"""
import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables
import requests
from datetime import datetime, timedelta
import json


# =============================================================================
# Configuration & Authentication
# =============================================================================

class GenesysAuth:
    """Handles OAuth2 authentication for Genesys Cloud"""

    def __init__(self, client_id, client_secret, region='mypurecloud.com'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region
        self.base_url = f"https://api.{region}"
        self.token = None
        self.token_expires = None

    def get_token(self):
        """Get or refresh OAuth token"""
        if self.token and self.token_expires and datetime.now() < self.token_expires:
            return self.token

        url = f"https://login.{self.region}/oauth/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data['access_token']
            self.token_expires = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600) - 60)
            return self.token
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

    def request(self, method, endpoint, **kwargs):
        """Make authenticated API request"""
        token = self.get_token()
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {token}'
        headers['Content-Type'] = 'application/json'
        kwargs['headers'] = headers

        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, **kwargs)

        if response.status_code >= 400:
            return {'success': False, 'error': f"API Error {response.status_code}: {response.text}"}

        try:
            data = response.json() if response.text else {}
            return {'success': True, 'data': data, 'status_code': response.status_code}
        except:
            return {'success': True, 'data': {}, 'status_code': response.status_code}


# =============================================================================
# Session Management
# =============================================================================

_sessions = {}  # Store auth objects by session ID

def _get_session():
    """Get current session auth object"""
    session_id = anvil.server.context.client.ip  # Or use a better session identifier
    return _sessions.get(session_id)

def _set_session(auth):
    """Store auth object for session"""
    session_id = anvil.server.context.client.ip
    _sessions[session_id] = auth


# =============================================================================
# Server Functions: Authentication
# =============================================================================

@anvil.server.callable
def connect_genesys(client_id, client_secret, region):
    """Connect to Genesys Cloud with OAuth credentials"""
    try:
        auth = GenesysAuth(client_id, client_secret, region)
        # Test connection
        auth.get_token()
        _set_session(auth)
        return {'success': True, 'message': 'Connected successfully'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@anvil.server.callable
def disconnect_genesys():
    """Disconnect from Genesys Cloud"""
    session_id = anvil.server.context.client.ip
    if session_id in _sessions:
        del _sessions[session_id]
    return {'success': True}


@anvil.server.callable
def is_connected():
    """Check if connected to Genesys Cloud"""
    return _get_session() is not None


# =============================================================================
# Server Functions: Users API
# =============================================================================

@anvil.server.callable
def users_list_page(page_size=25, page_number=1):
    """Get paginated list of users"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    endpoint = f"/api/v2/users?pageSize={page_size}&pageNumber={page_number}"
    return auth.request('GET', endpoint)


@anvil.server.callable
def users_search(query):
    """Search users by name"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    endpoint = f"/api/v2/users/search?query={query}"
    return auth.request('GET', endpoint)


@anvil.server.callable
def users_search_by_email(email):
    """Search for user by email"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    result = auth.request('GET', f"/api/v2/users/search?query={email}")
    if result['success'] and result['data'].get('results'):
        for user in result['data']['results']:
            if user.get('email', '').lower() == email.lower():
                return {'success': True, 'data': user}
    return {'success': False, 'error': 'User not found'}


@anvil.server.callable
def users_get(user_id):
    """Get user by ID"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    return auth.request('GET', f"/api/v2/users/{user_id}")


@anvil.server.callable
def users_update(user_id, data):
    """Update user profile"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    return auth.request('PATCH', f"/api/v2/users/{user_id}", json=data)


@anvil.server.callable
def users_bulk_update(updates):
    """
    Bulk update users
    updates: list of {'user_id': str, 'payload': dict}
    Returns: {'success': bool, 'results': list}
    """
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    results = []
    for update in updates:
        result = auth.request('PATCH', f"/api/v2/users/{update['user_id']}", json=update['payload'])
        results.append({
            'user_id': update['user_id'],
            'success': result['success'],
            'error': result.get('error')
        })

    success_count = sum(1 for r in results if r['success'])
    return {
        'success': True,
        'total': len(results),
        'success_count': success_count,
        'error_count': len(results) - success_count,
        'results': results
    }


@anvil.server.callable
def users_get_groups(user_id):
    """Get groups for a user"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    return auth.request('GET', f"/api/v2/users/{user_id}/groups")


@anvil.server.callable
def users_get_queues(user_id):
    """Get queues for a user"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    endpoint = f"/api/v2/users/{user_id}/queues"
    result = auth.request('GET', endpoint)
    if result['success']:
        return {'success': True, 'data': result['data'].get('entities', [])}
    return result


# =============================================================================
# Server Functions: Groups API
# =============================================================================

@anvil.server.callable
def groups_list_page(page_size=25, page_number=1):
    """Get paginated list of groups"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    endpoint = f"/api/v2/groups?pageSize={page_size}&pageNumber={page_number}"
    return auth.request('GET', endpoint)


@anvil.server.callable
def groups_get(group_id):
    """Get group by ID"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    return auth.request('GET', f"/api/v2/groups/{group_id}")


@anvil.server.callable
def groups_get_members(group_id):
    """Get members of a group"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    result = auth.request('GET', f"/api/v2/groups/{group_id}/members")
    if result['success']:
        return {'success': True, 'data': result['data'].get('entities', [])}
    return result


@anvil.server.callable
def groups_add_members(group_id, user_ids):
    """Add members to a group"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    return auth.request('POST', f"/api/v2/groups/{group_id}/members", json={'memberIds': user_ids})


@anvil.server.callable
def groups_remove_members(group_id, user_ids):
    """Remove members from a group"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    ids_param = ','.join(user_ids)
    return auth.request('DELETE', f"/api/v2/groups/{group_id}/members?id={ids_param}")


@anvil.server.callable
def groups_create(name, description='', group_type='official', visibility='public'):
    """Create a new group"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    payload = {
        'name': name,
        'description': description,
        'type': group_type,
        'visibility': visibility
    }
    return auth.request('POST', '/api/v2/groups', json=payload)


@anvil.server.callable
def groups_update(group_id, data):
    """Update a group"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    return auth.request('PUT', f"/api/v2/groups/{group_id}", json=data)


@anvil.server.callable
def groups_delete(group_id):
    """Delete a group"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    return auth.request('DELETE', f"/api/v2/groups/{group_id}")


# =============================================================================
# Server Functions: Queues API
# =============================================================================

@anvil.server.callable
def queues_list_page(page_size=25, page_number=1):
    """Get paginated list of queues"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    endpoint = f"/api/v2/routing/queues?pageSize={page_size}&pageNumber={page_number}"
    return auth.request('GET', endpoint)


@anvil.server.callable
def queues_get_members(queue_id):
    """Get members of a queue"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    result = auth.request('GET', f"/api/v2/routing/queues/{queue_id}/members")
    if result['success']:
        return {'success': True, 'data': result['data'].get('entities', [])}
    return result


# =============================================================================
# Server Functions: Skills/Routing API
# =============================================================================

@anvil.server.callable
def routing_get_skills():
    """Get all routing skills"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    result = auth.request('GET', '/api/v2/routing/skills')
    if result['success']:
        return {'success': True, 'data': result['data'].get('entities', [])}
    return result


@anvil.server.callable
def routing_get_user_skills(user_id):
    """Get skills for a user"""
    auth = _get_session()
    if not auth:
        return {'success': False, 'error': 'Not connected'}

    result = auth.request('GET', f"/api/v2/users/{user_id}/routingskills")
    if result['success']:
        return {'success': True, 'data': result['data'].get('entities', [])}
    return result
