"""
Configuration management for Genesys Cloud utilities.
"""

import os
import json
from typing import Optional, Dict
from dataclasses import dataclass


# Genesys Cloud regions
REGIONS = {
    "us-east-1": "mypurecloud.com",
    "us-west-2": "usw2.pure.cloud",
    "ca-central-1": "cac1.pure.cloud",
    "eu-west-1": "mypurecloud.ie",
    "eu-west-2": "euw2.pure.cloud",
    "eu-central-1": "mypurecloud.de",
    "ap-southeast-2": "mypurecloud.com.au",
    "ap-northeast-1": "mypurecloud.jp",
    "ap-northeast-2": "apne2.pure.cloud",
    "ap-south-1": "aps1.pure.cloud",
    "sa-east-1": "sae1.pure.cloud",
    "me-central-1": "mec1.pure.cloud",
}


@dataclass
class GenesysConfig:
    """Genesys Cloud configuration."""
    client_id: str
    client_secret: str
    region: str = "mypurecloud.com"
    source: str = "manual"

    @property
    def auth_url(self) -> str:
        return f"https://login.{self.region}"

    @property
    def api_url(self) -> str:
        return f"https://api.{self.region}"


def get_regions() -> list[str]:
    """Get list of available Genesys Cloud regions."""
    return list(REGIONS.values())


def load_config(
    config_path: str = "config.json",
    env_prefix: str = "GENESYS"
) -> Optional[GenesysConfig]:
    """
    Load Genesys Cloud configuration.

    Priority:
    1. Environment variables ({env_prefix}_CLIENT_ID, {env_prefix}_CLIENT_SECRET, {env_prefix}_REGION)
    2. Config file (JSON with client_id, client_secret, region)

    Args:
        config_path: Path to JSON config file
        env_prefix: Prefix for environment variables

    Returns:
        GenesysConfig if credentials found, None otherwise
    """
    # Try environment variables first
    client_id = os.environ.get(f'{env_prefix}_CLIENT_ID')
    client_secret = os.environ.get(f'{env_prefix}_CLIENT_SECRET')
    region = os.environ.get(f'{env_prefix}_REGION', 'mypurecloud.com')

    if client_id and client_secret:
        return GenesysConfig(
            client_id=client_id,
            client_secret=client_secret,
            region=region,
            source='environment'
        )

    # Fall back to config file
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            return GenesysConfig(
                client_id=data['client_id'],
                client_secret=data['client_secret'],
                region=data.get('region', 'mypurecloud.com'),
                source='file'
            )
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return None


def save_config(config: GenesysConfig, config_path: str = "config.json") -> bool:
    """
    Save configuration to file.

    Args:
        config: GenesysConfig to save
        config_path: Path to save to

    Returns:
        True if successful
    """
    try:
        with open(config_path, 'w') as f:
            json.dump({
                'client_id': config.client_id,
                'client_secret': config.client_secret,
                'region': config.region
            }, f, indent=2)
        return True
    except Exception:
        return False
