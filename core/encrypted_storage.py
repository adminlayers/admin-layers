"""
Encrypted Storage Module
Provides encrypted local storage for credentials, session data, and action history.

Works in both local and hosted (Streamlit Community Cloud) environments:
- Local: Encrypts data on disk at ~/.admin_layers/
- Hosted: Encrypts data in session state with key from st.secrets or auto-generated

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

import streamlit as st
from cryptography.fernet import Fernet, InvalidToken


class EncryptedStorage:
    """
    Encrypted key-value storage for sensitive data.

    Encryption key priority:
    1. st.secrets["encryption_key"] (for Streamlit Community Cloud)
    2. ADMIN_LAYERS_KEY environment variable
    3. Auto-generated per-session key (stored in session state)

    Storage backend priority:
    1. Local filesystem (~/.admin_layers/) when writable
    2. Session state (for hosted/ephemeral environments)
    """

    def __init__(self):
        self._fernet: Optional[Fernet] = None
        self._storage_dir: Optional[str] = None
        self._init_encryption()
        self._init_storage_dir()

    def _init_encryption(self) -> None:
        """Initialize the encryption key."""
        key = None

        # 1. Try st.secrets
        try:
            secret_key = st.secrets.get("encryption_key")
            if secret_key:
                key = self._derive_key(secret_key)
        except (FileNotFoundError, KeyError, AttributeError):
            pass

        # 2. Try environment variable
        if key is None:
            env_key = os.environ.get("ADMIN_LAYERS_KEY")
            if env_key:
                key = self._derive_key(env_key)

        # 3. Auto-generate per-session key
        if key is None:
            if "_encryption_key" not in st.session_state:
                st.session_state._encryption_key = Fernet.generate_key().decode()
            key = st.session_state._encryption_key.encode()

        self._fernet = Fernet(key)

    def _derive_key(self, passphrase: str) -> bytes:
        """Derive a Fernet-compatible key from a passphrase."""
        digest = hashlib.sha256(passphrase.encode()).digest()
        return base64.urlsafe_b64encode(digest)

    def _init_storage_dir(self) -> None:
        """Initialize local storage directory if available."""
        # Try home directory first
        try:
            storage_dir = os.path.join(Path.home(), ".admin_layers")
            os.makedirs(storage_dir, exist_ok=True)
            # Test write access
            test_file = os.path.join(storage_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            self._storage_dir = storage_dir
        except (OSError, PermissionError):
            # Fall back to temp directory
            try:
                storage_dir = os.path.join(tempfile.gettempdir(), ".admin_layers")
                os.makedirs(storage_dir, exist_ok=True)
                self._storage_dir = storage_dir
            except (OSError, PermissionError):
                # No filesystem access - use session state only
                self._storage_dir = None

    @property
    def is_persistent(self) -> bool:
        """Whether storage persists across sessions."""
        # Persistent if using file storage with a stable key (not auto-generated)
        has_stable_key = False
        try:
            has_stable_key = bool(st.secrets.get("encryption_key"))
        except (FileNotFoundError, KeyError, AttributeError):
            pass
        if not has_stable_key:
            has_stable_key = bool(os.environ.get("ADMIN_LAYERS_KEY"))
        return self._storage_dir is not None and has_stable_key

    def encrypt(self, data: str) -> str:
        """Encrypt a string and return base64-encoded ciphertext."""
        assert self._fernet is not None, "Encryption not initialized"
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """Decrypt base64-encoded ciphertext. Returns None on failure."""
        try:
            assert self._fernet is not None, "Encryption not initialized"
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        except (InvalidToken, Exception):
            return None

    def store(self, key: str, value: Any) -> bool:
        """
        Store a value with encryption.

        Args:
            key: Storage key
            value: Value to store (will be JSON-serialized then encrypted)

        Returns:
            True if stored successfully
        """
        try:
            json_data = json.dumps(value, default=str)
            encrypted = self.encrypt(json_data)

            # Store in session state (always)
            if "_encrypted_store" not in st.session_state:
                st.session_state._encrypted_store = {}
            st.session_state._encrypted_store[key] = encrypted

            # Also persist to file if available
            if self._storage_dir:
                file_path = os.path.join(self._storage_dir, f"{key}.enc")
                with open(file_path, "w") as f:
                    f.write(encrypted)

            return True
        except Exception:
            return False

    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve and decrypt a stored value.

        Args:
            key: Storage key

        Returns:
            Decrypted value or None if not found/decryption fails
        """
        encrypted = None

        # Try session state first (fastest)
        store = st.session_state.get("_encrypted_store", {})
        encrypted = store.get(key)

        # Fall back to file storage
        if encrypted is None and self._storage_dir:
            file_path = os.path.join(self._storage_dir, f"{key}.enc")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as f:
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
            store = st.session_state.get("_encrypted_store", {})
            store.pop(key, None)

            if self._storage_dir:
                file_path = os.path.join(self._storage_dir, f"{key}.enc")
                if os.path.exists(file_path):
                    os.remove(file_path)

            return True
        except Exception:
            return False

    def store_credentials(
        self, client_id: str, client_secret: str, region: str
    ) -> bool:
        """Store Genesys Cloud credentials encrypted."""
        return self.store(
            "gc_credentials",
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "region": region,
                "stored_at": datetime.now().isoformat(),
            },
        )

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

    # =========================================================================
    # Multiple Profiles Support
    # =========================================================================

    def store_profiles(self, profiles: list) -> bool:
        """Store list of user profiles encrypted."""
        return self.store("user_profiles", profiles)

    def retrieve_profiles(self) -> list:
        """Retrieve stored user profiles. Returns empty list if none."""
        return self.retrieve("user_profiles") or []

    def add_profile(self, profile: Dict[str, str]) -> str:
        """
        Add a new profile and return its ID.

        Profile should contain: name, email, company (optional)
        """
        import uuid

        profiles = self.retrieve_profiles()
        profile_id = str(uuid.uuid4())[:8]
        profile_data = {
            "id": profile_id,
            "name": profile.get("name", ""),
            "email": profile.get("email", ""),
            "company": profile.get("company", ""),
            "created_at": datetime.now().isoformat(),
        }
        profiles.append(profile_data)
        self.store_profiles(profiles)
        return profile_id

    def update_profile(self, profile_id: str, profile: Dict[str, str]) -> bool:
        """Update an existing profile by ID."""
        profiles = self.retrieve_profiles()
        for i, p in enumerate(profiles):
            if p.get("id") == profile_id:
                profiles[i] = {
                    **p,
                    "name": profile.get("name", p.get("name", "")),
                    "email": profile.get("email", p.get("email", "")),
                    "company": profile.get("company", p.get("company", "")),
                    "updated_at": datetime.now().isoformat(),
                }
                return self.store_profiles(profiles)
        return False

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile by ID."""
        profiles = self.retrieve_profiles()
        profiles = [p for p in profiles if p.get("id") != profile_id]
        return self.store_profiles(profiles)

    def get_profile(self, profile_id: str) -> Optional[Dict[str, str]]:
        """Get a specific profile by ID."""
        profiles = self.retrieve_profiles()
        for p in profiles:
            if p.get("id") == profile_id:
                return p
        return None

    def set_active_profile(self, profile_id: str) -> bool:
        """Set the active profile ID."""
        return self.store("active_profile_id", profile_id)

    def get_active_profile_id(self) -> Optional[str]:
        """Get the active profile ID."""
        return self.retrieve("active_profile_id")

    def get_active_profile(self) -> Optional[Dict[str, str]]:
        """Get the currently active profile."""
        profile_id = self.get_active_profile_id()
        if profile_id:
            return self.get_profile(profile_id)
        return None

    # =========================================================================
    # OpenRouter / Chat API Key Storage
    # =========================================================================

    def store_openrouter_key(self, api_key: str) -> bool:
        """Store OpenRouter API key encrypted."""
        return self.store(
            "openrouter_api_key",
            {
                "api_key": api_key,
                "stored_at": datetime.now().isoformat(),
            },
        )

    def retrieve_openrouter_key(self) -> Optional[str]:
        """Retrieve stored OpenRouter API key."""
        data = self.retrieve("openrouter_api_key")
        if data and isinstance(data, dict):
            return data.get("api_key")
        return None

    def clear_openrouter_key(self) -> bool:
        """Clear stored OpenRouter API key."""
        return self.delete("openrouter_api_key")

    # =========================================================================
    # Chat Settings Storage
    # =========================================================================

    def store_chat_settings(self, settings: Dict[str, Any]) -> bool:
        """Store chat settings (model, system prompt, etc.)."""
        return self.store("chat_settings", settings)

    def retrieve_chat_settings(self) -> Optional[Dict[str, Any]]:
        """Retrieve chat settings."""
        return self.retrieve("chat_settings")

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
        has_secrets_key = False
        try:
            has_secrets_key = bool(st.secrets.get("encryption_key"))
        except (FileNotFoundError, KeyError, AttributeError):
            pass

        has_env_key = bool(os.environ.get("ADMIN_LAYERS_KEY"))

        return {
            "backend": "filesystem" if self._storage_dir else "session_state",
            "storage_dir": self._storage_dir,
            "persistent": self.is_persistent,
            "key_source": (
                "st.secrets"
                if has_secrets_key
                else "environment" if has_env_key else "session (auto-generated)"
            ),
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
