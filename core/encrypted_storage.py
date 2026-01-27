"""
Encrypted Storage Module
Provides encrypted local storage for credentials, session data, and action history.

Works in both local and hosted environments:
- Local: Encrypts data on disk at ~/.admin_layers/
- Hosted: Encrypts data in memory with key from environment or auto-generated

All sensitive data (credentials, tokens, history) is encrypted at rest using
Fernet symmetric encryption (AES-128-CBC with HMAC-SHA256).
"""

import base64
import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken


# Module-level in-memory store (replaces session state)
_memory_store: Dict[str, str] = {}
_session_key: Optional[str] = None


class EncryptedStorage:
    """
    Encrypted key-value storage for sensitive data.

    Encryption key priority:
    1. ADMIN_LAYERS_KEY environment variable
    2. Auto-generated per-process key (stored in module variable)

    Storage backend priority:
    1. Local filesystem (~/.admin_layers/) when writable
    2. In-memory store (for hosted/ephemeral environments)
    """

    def __init__(self):
        self._fernet: Optional[Fernet] = None
        self._storage_dir: Optional[str] = None
        self._init_encryption()
        self._init_storage_dir()

    def _init_encryption(self) -> None:
        """Initialize the encryption key."""
        global _session_key
        key = None

        # 1. Try environment variable
        env_key = os.environ.get("ADMIN_LAYERS_KEY")
        if env_key:
            key = self._derive_key(env_key)

        # 2. Auto-generate per-process key
        if key is None:
            if _session_key is None:
                _session_key = Fernet.generate_key().decode()
            key = _session_key.encode()

        self._fernet = Fernet(key)

    def _derive_key(self, passphrase: str) -> bytes:
        """Derive a Fernet-compatible key from a passphrase."""
        digest = hashlib.sha256(passphrase.encode()).digest()
        return base64.urlsafe_b64encode(digest)

    def _init_storage_dir(self) -> None:
        """Initialize local storage directory if available."""
        try:
            storage_dir = os.path.join(Path.home(), '.admin_layers')
            os.makedirs(storage_dir, exist_ok=True)
            test_file = os.path.join(storage_dir, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            self._storage_dir = storage_dir
        except (OSError, PermissionError):
            try:
                storage_dir = os.path.join(tempfile.gettempdir(), '.admin_layers')
                os.makedirs(storage_dir, exist_ok=True)
                self._storage_dir = storage_dir
            except (OSError, PermissionError):
                self._storage_dir = None

    @property
    def is_persistent(self) -> bool:
        """Whether storage persists across sessions."""
        has_stable_key = bool(os.environ.get("ADMIN_LAYERS_KEY"))
        return self._storage_dir is not None and has_stable_key

    def encrypt(self, data: str) -> str:
        """Encrypt a string and return base64-encoded ciphertext."""
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """Decrypt base64-encoded ciphertext. Returns None on failure."""
        try:
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        except (InvalidToken, Exception):
            return None

    def store(self, key: str, value: Any) -> bool:
        """Store a value with encryption."""
        try:
            json_data = json.dumps(value, default=str)
            encrypted = self.encrypt(json_data)

            # Store in memory
            _memory_store[key] = encrypted

            # Also persist to file if available
            if self._storage_dir:
                file_path = os.path.join(self._storage_dir, f"{key}.enc")
                with open(file_path, 'w') as f:
                    f.write(encrypted)

            return True
        except Exception:
            return False

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve and decrypt a stored value."""
        encrypted = None

        # Try memory first
        encrypted = _memory_store.get(key)

        # Fall back to file storage
        if encrypted is None and self._storage_dir:
            file_path = os.path.join(self._storage_dir, f"{key}.enc")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        encrypted = f.read().strip()
                except (OSError, IOError):
                    pass

        if encrypted is None:
            return None

        decrypted = self.decrypt(encrypted)
        if decrypted is None:
            return None

        try:
            return json.loads(decrypted)
        except json.JSONDecodeError:
            return decrypted

    def delete(self, key: str) -> bool:
        """Delete a stored value."""
        try:
            _memory_store.pop(key, None)

            if self._storage_dir:
                file_path = os.path.join(self._storage_dir, f"{key}.enc")
                if os.path.exists(file_path):
                    os.remove(file_path)

            return True
        except Exception:
            return False

    def store_credentials(self, client_id: str, client_secret: str, region: str) -> bool:
        """Store Genesys Cloud credentials encrypted."""
        return self.store("gc_credentials", {
            "client_id": client_id,
            "client_secret": client_secret,
            "region": region,
            "stored_at": datetime.now().isoformat()
        })

    def retrieve_credentials(self) -> Optional[Dict[str, str]]:
        """Retrieve stored credentials."""
        return self.retrieve("gc_credentials")

    def clear_credentials(self) -> bool:
        """Clear stored credentials."""
        return self.delete("gc_credentials")

    def store_local_user(self, profile: Dict[str, str]) -> bool:
        """Store local user profile metadata encrypted."""
        payload = {
            **profile,
            "stored_at": datetime.now().isoformat(),
        }
        return self.store("local_user_profile", payload)

    def retrieve_local_user(self) -> Optional[Dict[str, str]]:
        """Retrieve stored local user profile."""
        return self.retrieve("local_user_profile")

    def clear_local_user(self) -> bool:
        """Clear stored local user profile."""
        return self.delete("local_user_profile")

    def store_session(self, session_data: Dict) -> bool:
        """Store session state data encrypted."""
        return self.store("session_data", session_data)

    def retrieve_session(self) -> Optional[Dict]:
        """Retrieve encrypted session data."""
        return self.retrieve("session_data")

    def store_history(self, history: list) -> bool:
        """Store action history encrypted."""
        return self.store("action_history", history)

    def retrieve_history(self) -> Optional[list]:
        """Retrieve encrypted action history."""
        return self.retrieve("action_history")

    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage configuration info for display."""
        has_env_key = bool(os.environ.get("ADMIN_LAYERS_KEY"))

        return {
            "backend": "filesystem" if self._storage_dir else "memory",
            "storage_dir": self._storage_dir,
            "persistent": self.is_persistent,
            "key_source": "environment" if has_env_key else "process (auto-generated)",
            "encryption": "Fernet (AES-128-CBC + HMAC-SHA256)",
        }


# Singleton
_storage_instance: Optional[EncryptedStorage] = None


def get_storage() -> EncryptedStorage:
    """Get the global encrypted storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = EncryptedStorage()
    return _storage_instance
