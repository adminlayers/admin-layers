"""
Authentication module for Genesys Cloud.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple

import requests

from .config import GenesysConfig, load_config


@dataclass
class AuthToken:
    """OAuth token with metadata."""

    access_token: str
    token_type: str
    expires_in: int
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def expires_at(self) -> datetime:
        return self.created_at + timedelta(seconds=self.expires_in)

    @property
    def is_expired(self) -> bool:
        # Consider expired 60 seconds before actual expiry
        return datetime.now() >= (self.expires_at - timedelta(seconds=60))


class GenesysAuth:
    """
    Genesys Cloud OAuth authentication handler.

    Supports:
    - Client credentials grant (service accounts)
    - Automatic token refresh
    - Multiple configuration sources

    Usage:
        auth = GenesysAuth.from_config()
        if auth.authenticate():
            token = auth.token
    """

    def __init__(self, config: GenesysConfig):
        """
        Initialize with configuration.

        Args:
            config: GenesysConfig with credentials
        """
        self.config = config
        self._token: Optional[AuthToken] = None

    @classmethod
    def from_config(
        cls, config_path: str = "config.json", env_prefix: str = "GENESYS"
    ) -> Optional["GenesysAuth"]:
        """
        Create GenesysAuth from configuration file or environment.

        Args:
            config_path: Path to JSON config file
            env_prefix: Prefix for environment variables

        Returns:
            GenesysAuth instance or None if no config found
        """
        config = load_config(config_path, env_prefix)
        if config:
            return cls(config)
        return None

    @classmethod
    def from_credentials(
        cls, client_id: str, client_secret: str, region: str = "mypurecloud.com"
    ) -> "GenesysAuth":
        """
        Create GenesysAuth from explicit credentials.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            region: Genesys Cloud region

        Returns:
            GenesysAuth instance
        """
        config = GenesysConfig(
            client_id=client_id,
            client_secret=client_secret,
            region=region,
            source="manual",
        )
        return cls(config)

    @property
    def token(self) -> Optional[AuthToken]:
        """Current auth token."""
        return self._token

    @property
    def access_token(self) -> Optional[str]:
        """Current access token string."""
        return self._token.access_token if self._token else None

    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated with valid token."""
        return self._token is not None and not self._token.is_expired

    def authenticate(self) -> Tuple[bool, str]:
        """
        Authenticate with Genesys Cloud using client credentials.

        Returns:
            Tuple of (success: bool, message: str)
        """
        token_url = f"{self.config.auth_url}/oauth/token"

        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        try:
            response = requests.post(token_url, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()
            self._token = AuthToken(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 86400),
            )

            return True, "Authentication successful"

        except requests.exceptions.Timeout:
            return False, "Authentication timed out"
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get(
                        "error_description", error_data.get("error", str(e))
                    )
                except:
                    error_msg = e.response.text
            return False, f"Authentication failed: {error_msg}"

    def refresh_if_needed(self) -> bool:
        """
        Refresh token if expired or about to expire.

        Returns:
            True if token is valid (refreshed or still valid)
        """
        if self._token is None:
            success, _ = self.authenticate()
            return success

        if self._token.is_expired:
            success, _ = self.authenticate()
            return success

        return True

    def get_headers(self) -> dict:
        """
        Get HTTP headers for authenticated API requests.

        Returns:
            Dict with Authorization header

        Raises:
            ValueError if not authenticated
        """
        if not self.is_authenticated:
            raise ValueError("Not authenticated. Call authenticate() first.")

        return {
            "Authorization": f"Bearer {self._token.access_token}",
            "Content-Type": "application/json",
        }
