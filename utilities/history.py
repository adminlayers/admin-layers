# -*- coding: utf-8 -*-
"""
Action History Module
Stores all operations locally for audit and rollback purposes.
Supports both local filesystem and in-memory backends.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


# Module-level in-memory history store (replaces st.session_state fallback)
_memory_history: list = []


@dataclass
class ActionRecord:
    """Record of a single action."""
    id: str
    timestamp: str
    utility: str
    action: str
    target: str  # e.g., group name, queue name
    target_id: str
    details: Dict[str, Any]
    affected_count: int
    status: str  # 'success', 'failed', 'partial'
    user_ids: List[str]  # IDs affected for potential rollback


class ActionHistory:
    """
    Local action history storage.
    Stores all operations for audit and rollback.

    Backend priority:
    1. Local filesystem (~/.admin_layers/action_history.json)
    2. In-memory store (for cloud/ephemeral environments)

    When encrypted storage is available, history is also
    persisted to encrypted storage for cross-session access.
    """

    def __init__(self, storage_dir: str = None):
        """Initialize history storage."""
        self._use_filesystem = False
        self.storage_dir = None
        self.history_file = None

        if storage_dir is None:
            try:
                storage_dir = os.path.join(Path.home(), '.admin_layers')
                os.makedirs(storage_dir, exist_ok=True)
                # Test write access
                test_path = os.path.join(storage_dir, '.write_test')
                with open(test_path, 'w') as f:
                    f.write('test')
                os.remove(test_path)
                self._use_filesystem = True
            except (OSError, PermissionError):
                self._use_filesystem = False
        else:
            try:
                os.makedirs(storage_dir, exist_ok=True)
                self._use_filesystem = True
            except (OSError, PermissionError):
                self._use_filesystem = False

        if self._use_filesystem:
            self.storage_dir = storage_dir
            self.history_file = os.path.join(storage_dir, 'action_history.json')

        # Load existing history
        self._history: List[Dict] = self._load_history()

    def _load_history(self) -> List[Dict]:
        """Load history from filesystem or session state."""
        # Try filesystem first
        if self._use_filesystem and self.history_file:
            if os.path.exists(self.history_file):
                try:
                    with open(self.history_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass

        # Fall back to in-memory store
        return list(_memory_history)

    def _save_history(self) -> None:
        """Save history to filesystem and session state."""
        # Always save to in-memory store
        global _memory_history
        _memory_history = list(self._history)

        # Also save to filesystem if available
        if self._use_filesystem and self.history_file:
            try:
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(self._history, f, indent=2, ensure_ascii=False)
            except (IOError, OSError):
                pass

    def _generate_id(self) -> str:
        """Generate a unique action ID."""
        return datetime.now().strftime('%Y%m%d_%H%M%S_%f')

    def record_action(
        self,
        utility: str,
        action: str,
        target: str,
        target_id: str,
        details: Dict[str, Any],
        affected_count: int,
        status: str,
        user_ids: List[str] = None
    ) -> str:
        """
        Record an action to history.

        Args:
            utility: Name of utility (e.g., 'group_manager')
            action: Action type (e.g., 'add_members', 'remove_members')
            target: Human-readable target (e.g., group name)
            target_id: Target ID (e.g., group ID)
            details: Additional details about the action
            affected_count: Number of items affected
            status: 'success', 'failed', or 'partial'
            user_ids: List of user IDs affected (for rollback)

        Returns:
            Action ID
        """
        action_id = self._generate_id()

        record = ActionRecord(
            id=action_id,
            timestamp=datetime.now().isoformat(),
            utility=utility,
            action=action,
            target=target,
            target_id=target_id,
            details=details,
            affected_count=affected_count,
            status=status,
            user_ids=user_ids or []
        )

        self._history.insert(0, asdict(record))  # Most recent first

        # Keep only last 500 actions
        self._history = self._history[:500]

        self._save_history()

        return action_id

    def get_history(
        self,
        utility: str = None,
        action: str = None,
        target_id: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get filtered history.

        Args:
            utility: Filter by utility name
            action: Filter by action type
            target_id: Filter by target ID
            limit: Maximum records to return

        Returns:
            List of action records
        """
        results = self._history

        if utility:
            results = [r for r in results if r.get('utility') == utility]

        if action:
            results = [r for r in results if r.get('action') == action]

        if target_id:
            results = [r for r in results if r.get('target_id') == target_id]

        return results[:limit]

    def get_action(self, action_id: str) -> Optional[Dict]:
        """Get a specific action by ID."""
        for record in self._history:
            if record.get('id') == action_id:
                return record
        return None

    def get_rollback_data(self, action_id: str) -> Optional[Dict]:
        """
        Get data needed to rollback an action.

        Returns:
            Dict with target_id and user_ids if action is rollback-able
        """
        action = self.get_action(action_id)
        if not action:
            return None

        if action.get('status') != 'success':
            return None

        if action.get('action') not in ['add_members', 'remove_members']:
            return None

        return {
            'target_id': action.get('target_id'),
            'user_ids': action.get('user_ids', []),
            'original_action': action.get('action')
        }

    def clear_history(self) -> None:
        """Clear all history."""
        self._history = []
        self._save_history()

    @property
    def backend_info(self) -> str:
        """Get info about the current storage backend."""
        if self._use_filesystem:
            return f"filesystem ({self.storage_dir})"
        return "in-memory (ephemeral)"


# Global instance
_history_instance: Optional[ActionHistory] = None


def get_history() -> ActionHistory:
    """Get the global history instance."""
    global _history_instance
    if _history_instance is None:
        _history_instance = ActionHistory()
    return _history_instance
