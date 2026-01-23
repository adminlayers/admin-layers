# Genesys Cloud Utilities Suite

## Commercial Documentation

A modular, extensible Python framework for building Genesys Cloud administration utilities with a Streamlit-based web interface.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Module Structure](#module-structure)
3. [Core SDK (`genesys_cloud/`)](#core-sdk)
4. [Utility Framework (`utilities/`)](#utility-framework)
5. [Creating New Utilities](#creating-new-utilities)
6. [Configuration](#configuration)
7. [CI/CD Integration](#cicd-integration)
8. [Security Considerations](#security-considerations)
9. [API Reference](#api-reference)

---

## Architecture Overview

```
genesys-cloud-utilities/
â”œâ”€â”€ genesys_cloud/          # Core SDK - Authentication & API client
â”‚   â”œâ”€â”€ __init__.py         # Public exports
â”‚   â”œâ”€â”€ config.py           # Configuration management
â”‚   â”œâ”€â”€ auth.py             # OAuth authentication
â”‚   â””â”€â”€ api.py              # API client with sub-APIs
â”œâ”€â”€ utilities/              # Utility framework
â”‚   â”œâ”€â”€ __init__.py         # Public exports
â”‚   â”œâ”€â”€ base.py             # BaseUtility abstract class
â”‚   â””â”€â”€ group_manager.py    # Example utility implementation
â”œâ”€â”€ app.py                  # Streamlit application entry point
â”œâ”€â”€ config.json             # Local configuration (gitignore this)
â”œâ”€â”€ requirements.txt        # Python dependencies
â”œâ”€â”€ set_credentials.ps1     # Environment setup script
â””â”€â”€ .streamlit/
    â””â”€â”€ config.toml         # Streamlit theme configuration
```

### Design Principles

1. **Separation of Concerns**: SDK handles API communication; utilities handle UI/UX
2. **Plugin Architecture**: Utilities register themselves; app discovers them automatically
3. **Configuration Priority**: Environment variables > config file > manual input
4. **Standardized Responses**: All API calls return `APIResponse` objects
5. **Automatic Token Management**: Auth handles refresh automatically

---

## Module Structure

### Dependency Flow

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                         app.py                              â”‚
â”‚                    (Streamlit Entry Point)                  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â”‚
              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
              â–¼                               â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚     genesys_cloud/      â”‚     â”‚        utilities/           â”‚
â”‚  (Core SDK Package)     â”‚â—„â”€â”€â”€â”€â”‚   (Utility Framework)       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
              â”‚
    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â–¼         â–¼         â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”
â”‚config â”‚ â”‚ auth  â”‚ â”‚  api  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## Core SDK

### `genesys_cloud/config.py`

Manages configuration loading with environment variable priority.

```python
from genesys_cloud import load_config, get_regions, GenesysConfig

# Load configuration (env vars take priority over config.json)
config = load_config()

# Get available regions
regions = get_regions()
# Returns: ['mypurecloud.com', 'usw2.pure.cloud', 'mypurecloud.ie', ...]

# Create config manually
config = GenesysConfig(
    client_id="your-client-id",
    client_secret="your-client-secret",
    region="mypurecloud.com"
)

# Access computed properties
print(config.auth_url)  # https://login.mypurecloud.com
print(config.api_url)   # https://api.mypurecloud.com
```

**Supported Regions:**
| Region Code | Domain |
|-------------|--------|
| us-east-1 | mypurecloud.com |
| us-west-2 | usw2.pure.cloud |
| ca-central-1 | cac1.pure.cloud |
| eu-west-1 | mypurecloud.ie |
| eu-west-2 | euw2.pure.cloud |
| eu-central-1 | mypurecloud.de |
| ap-southeast-2 | mypurecloud.com.au |
| ap-northeast-1 | mypurecloud.jp |
| ap-northeast-2 | apne2.pure.cloud |
| ap-south-1 | aps1.pure.cloud |
| sa-east-1 | sae1.pure.cloud |
| me-central-1 | mec1.pure.cloud |

### `genesys_cloud/auth.py`

OAuth2 client credentials authentication with automatic token refresh.

```python
from genesys_cloud import GenesysAuth

# Option 1: From config file or environment
auth = GenesysAuth.from_config()

# Option 2: From explicit credentials
auth = GenesysAuth.from_credentials(
    client_id="your-client-id",
    client_secret="your-client-secret",
    region="mypurecloud.com"
)

# Authenticate
success, message = auth.authenticate()
if success:
    print(f"Token expires at: {auth.token.expires_at}")

# Check status
if auth.is_authenticated:
    headers = auth.get_headers()
    # {'Authorization': 'Bearer ...', 'Content-Type': 'application/json'}

# Auto-refresh (called internally by API client)
auth.refresh_if_needed()
```

**AuthToken Properties:**
- `access_token`: The bearer token string
- `token_type`: Token type (always "Bearer")
- `expires_in`: Seconds until expiration
- `expires_at`: DateTime of expiration
- `is_expired`: Boolean (includes 60s buffer)

### `genesys_cloud/api.py`

API client with sub-APIs for common operations.

```python
from genesys_cloud import GenesysAuth, GenesysCloudAPI

auth = GenesysAuth.from_config()
auth.authenticate()
api = GenesysCloudAPI(auth)

# Sub-APIs available:
api.users       # User operations
api.groups      # Group operations
api.queues      # Queue operations
api.conversations  # Conversation operations
api.routing     # Routing operations
```

**APIResponse Object:**
```python
@dataclass
class APIResponse:
    success: bool           # True if request succeeded
    data: Any = None        # Response JSON data
    error: str = None       # Error message if failed
    status_code: int = None # HTTP status code
```

**Generic Request Methods:**
```python
# Low-level methods (use sub-APIs instead when possible)
response = api.get('/api/v2/endpoint', params={'key': 'value'})
response = api.post('/api/v2/endpoint', json={'key': 'value'})
response = api.put('/api/v2/endpoint', json={'key': 'value'})
response = api.patch('/api/v2/endpoint', json={'key': 'value'})
response = api.delete('/api/v2/endpoint')

# Automatic pagination
for entity in api.paginate('/api/v2/users', page_size=100):
    print(entity['name'])
```

---

## Sub-API Reference

### UsersAPI (`api.users`)

```python
# Get user by ID
response = api.users.get("user-id")

# Search users (QUERY_STRING search)
users = api.users.search("john")

# Find user by exact email
user = api.users.search_by_email("john@example.com")

# List all users (generator)
for user in api.users.list(page_size=100, max_pages=10):
    print(user['email'])
```

### GroupsAPI (`api.groups`)

```python
# Get group by ID
response = api.groups.get("group-id")

# Search groups by name
groups = api.groups.search("Support")

# Get group members
members = api.groups.get_members("group-id")

# Add members to group
response = api.groups.add_members("group-id", ["user-id-1", "user-id-2"])

# Remove members from group
response = api.groups.remove_members("group-id", ["user-id-1"])

# List all groups (generator)
for group in api.groups.list():
    print(group['name'])
```

### QueuesAPI (`api.queues`)

```python
# Get queue by ID
response = api.queues.get("queue-id")

# Search queues by name
queues = api.queues.search("Sales")

# Get queue members
members = api.queues.get_members("queue-id")

# List all queues (generator)
for queue in api.queues.list():
    print(queue['name'])
```

### ConversationsAPI (`api.conversations`)

```python
# Get conversation by ID
response = api.conversations.get("conversation-id")

# Get conversation analytics details
response = api.conversations.get_details("conversation-id")

# Disconnect a conversation
response = api.conversations.disconnect("conversation-id")

# Query conversations by interval
conversations = api.conversations.query(
    interval="2024-01-01T00:00:00Z/2024-01-02T00:00:00Z",
    filters=[{
        "type": "dimension",
        "dimension": "queueId",
        "operator": "matches",
        "value": "queue-id"
    }],
    page_size=100
)
```

### RoutingAPI (`api.routing`)

```python
# Get all skills
skills = api.routing.get_skills()

# Get all languages
languages = api.routing.get_languages()

# Get all wrapup codes
wrapup_codes = api.routing.get_wrapup_codes()

# Get user's skills
user_skills = api.routing.get_user_skills("user-id")

# Add skill to user
response = api.routing.add_user_skill("user-id", "skill-id", proficiency=0.8)

# Remove skill from user
response = api.routing.remove_user_skill("user-id", "skill-id")
```

---

## Utility Framework

### `utilities/base.py`

Base class that all utilities must inherit from.

```python
from utilities import BaseUtility, UtilityConfig

class MyUtility(BaseUtility):
    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="my_utility",           # Unique identifier
            name="My Utility",         # Display name
            description="Description", # Short description
            icon="ðŸ”§",                 # Emoji icon
            category="General",        # Category for grouping
            requires_group=False,      # Requires group selection
            requires_queue=False,      # Requires queue selection
            requires_user=False,       # Requires user selection
            tags=["tag1", "tag2"]      # Searchable tags
        )

    def render_sidebar(self) -> None:
        """Render sidebar controls."""
        pass

    def render_main(self) -> None:
        """Render main content area."""
        pass

    # Optional overrides
    def init_state(self) -> None:
        """Initialize session state."""
        pass

    def cleanup(self) -> None:
        """Cleanup when switching utilities."""
        pass
```

**Helper Methods:**
```python
# Display messages
self.show_error("Error message")
self.show_success("Success message")
self.show_info("Info message")
self.show_warning("Warning message")

# Utility-scoped state (automatically prefixed with utility ID)
self.set_state('my_key', value)
value = self.get_state('my_key', default=None)
```

---

## Creating New Utilities

### Step 1: Create the Utility File

Create `utilities/my_utility.py`:

```python
"""
My Utility
Description of what this utility does.
"""

import streamlit as st
from typing import List, Dict
from .base import BaseUtility, UtilityConfig


class MyUtility(BaseUtility):
    """
    Docstring describing the utility.

    Features:
    - Feature 1
    - Feature 2
    """

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="my_utility",
            name="My Utility",
            description="Does something useful",
            icon="ðŸ› ï¸",
            category="Custom",
            tags=["custom", "example"]
        )

    def init_state(self) -> None:
        """Initialize utility state."""
        if self.get_state('initialized') is None:
            self.set_state('initialized', True)
            self.set_state('data', [])

    def render_sidebar(self) -> None:
        """Render sidebar controls."""
        st.markdown("#### Settings")

        if st.button("Refresh Data", use_container_width=True):
            self._load_data()

    def render_main(self) -> None:
        """Render main content."""
        self.init_state()

        st.markdown("## My Utility")

        data = self.get_state('data', [])
        if not data:
            st.info("No data loaded. Click Refresh in the sidebar.")
            return

        st.dataframe(data)

    def _load_data(self) -> None:
        """Load data from API."""
        with st.spinner("Loading..."):
            # Use self.api to make API calls
            users = list(self.api.users.list(max_pages=1))
            self.set_state('data', users)
            st.rerun()
```

### Step 2: Export from Package

Update `utilities/__init__.py`:

```python
from .base import BaseUtility, UtilityConfig
from .group_manager import GroupManagerUtility
from .my_utility import MyUtility  # Add this

__all__ = [
    'BaseUtility',
    'UtilityConfig',
    'GroupManagerUtility',
    'MyUtility'  # Add this
]
```

### Step 3: Register in App

Update `app.py`:

```python
from utilities import BaseUtility, GroupManagerUtility, MyUtility

UTILITIES: Dict[str, Type[BaseUtility]] = {
    "group_manager": GroupManagerUtility,
    "my_utility": MyUtility,  # Add this
}
```

The utility will now appear in the sidebar navigation automatically.

---

## Configuration

### Environment Variables

```bash
# Required
GENESYS_CLIENT_ID=your-client-id
GENESYS_CLIENT_SECRET=your-client-secret

# Optional (defaults to mypurecloud.com)
GENESYS_REGION=mypurecloud.com
```

### Config File (`config.json`)

```json
{
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "region": "mypurecloud.com"
}
```

**Priority Order:**
1. Environment variables (highest priority)
2. Config file
3. Manual input via UI

### Streamlit Theme (`.streamlit/config.toml`)

```toml
[theme]
primaryColor = "#4A6FA5"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F7FA"
textColor = "#1E2A38"
font = "sans serif"

[server]
headless = true

[browser]
gatherUsageStats = false
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: pytest tests/ --cov=genesys_cloud --cov=utilities

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Streamlit Cloud
        # Or your deployment target
        run: echo "Deploy step"
```

### Docker Support

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501

CMD ["streamlit", "run", "app.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GENESYS_CLIENT_ID=${GENESYS_CLIENT_ID}
      - GENESYS_CLIENT_SECRET=${GENESYS_CLIENT_SECRET}
      - GENESYS_REGION=${GENESYS_REGION:-mypurecloud.com}
```

### Testing Template

```python
# tests/test_api.py
import pytest
from unittest.mock import Mock, patch
from genesys_cloud import GenesysAuth, GenesysCloudAPI, GenesysConfig


@pytest.fixture
def mock_auth():
    auth = Mock(spec=GenesysAuth)
    auth.config = GenesysConfig(
        client_id="test",
        client_secret="test",
        region="mypurecloud.com"
    )
    auth.is_authenticated = True
    auth.refresh_if_needed.return_value = True
    auth.get_headers.return_value = {
        'Authorization': 'Bearer test-token',
        'Content-Type': 'application/json'
    }
    return auth


@pytest.fixture
def api(mock_auth):
    return GenesysCloudAPI(mock_auth)


def test_users_search(api):
    with patch.object(api, 'post') as mock_post:
        mock_post.return_value.success = True
        mock_post.return_value.data = {'results': [{'id': '123', 'name': 'Test'}]}

        results = api.users.search("test")

        assert len(results) == 1
        assert results[0]['name'] == 'Test'
```

---

## Security Considerations

### Credentials Management

1. **Never commit credentials** to version control
2. Add to `.gitignore`:
   ```
   config.json
   *.env
   .env*
   ```

3. Use environment variables in production
4. Rotate client secrets regularly

### API Permissions

Create OAuth clients with minimum required permissions:

| Utility | Required Permissions |
|---------|---------------------|
| Group Manager | `groups`, `users:readonly` |
| Queue Manager | `routing`, `users:readonly` |
| Conversation Tools | `conversations`, `analytics` |

### Session Security

- Tokens are stored in Streamlit session state (server-side)
- Session state is cleared on disconnect
- Consider implementing session timeout for production

---

## API Reference Quick Sheet

### Authentication
```python
GenesysAuth.from_config() -> Optional[GenesysAuth]
GenesysAuth.from_credentials(client_id, client_secret, region) -> GenesysAuth
auth.authenticate() -> Tuple[bool, str]
auth.refresh_if_needed() -> bool
auth.get_headers() -> dict
auth.is_authenticated -> bool
auth.access_token -> Optional[str]
```

### API Client
```python
GenesysCloudAPI(auth) -> GenesysCloudAPI
api.get(endpoint, params) -> APIResponse
api.post(endpoint, json, params) -> APIResponse
api.put(endpoint, json) -> APIResponse
api.patch(endpoint, json) -> APIResponse
api.delete(endpoint, params) -> APIResponse
api.paginate(endpoint, params, page_size, max_pages) -> Generator
```

### Sub-APIs
```python
# Users
api.users.get(user_id) -> APIResponse
api.users.search(query) -> List[Dict]
api.users.search_by_email(email) -> Optional[Dict]
api.users.list() -> Generator

# Groups
api.groups.get(group_id) -> APIResponse
api.groups.search(query) -> List[Dict]
api.groups.get_members(group_id) -> List[Dict]
api.groups.add_members(group_id, member_ids) -> APIResponse
api.groups.remove_members(group_id, member_ids) -> APIResponse
api.groups.list() -> Generator

# Queues
api.queues.get(queue_id) -> APIResponse
api.queues.search(query) -> List[Dict]
api.queues.get_members(queue_id) -> List[Dict]
api.queues.list() -> Generator

# Conversations
api.conversations.get(conversation_id) -> APIResponse
api.conversations.get_details(conversation_id) -> APIResponse
api.conversations.disconnect(conversation_id) -> APIResponse
api.conversations.query(interval, filters, page_size) -> List[Dict]

# Routing
api.routing.get_skills() -> List[Dict]
api.routing.get_languages() -> List[Dict]
api.routing.get_wrapup_codes() -> List[Dict]
api.routing.get_user_skills(user_id) -> List[Dict]
api.routing.add_user_skill(user_id, skill_id, proficiency) -> APIResponse
api.routing.remove_user_skill(user_id, skill_id) -> APIResponse
```

### Utility Base
```python
BaseUtility.get_config() -> UtilityConfig  # static, abstract
utility.render_sidebar() -> None           # abstract
utility.render_main() -> None              # abstract
utility.init_state() -> None               # optional override
utility.cleanup() -> None                  # optional override
utility.show_error(message) -> None
utility.show_success(message) -> None
utility.show_info(message) -> None
utility.show_warning(message) -> None
utility.get_state(key, default) -> Any
utility.set_state(key, value) -> None
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024 | Initial release |

---

## License

[Your License Here]

---

## Support

[Your Support Information Here]
