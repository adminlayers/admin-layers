"""
Base utility class for Genesys Cloud utilities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import streamlit as st


@dataclass
class UtilityConfig:
    """
    Configuration for a utility module.

    Attributes:
        id: Unique identifier for the utility
        name: Display name
        description: Short description
        icon: Emoji or icon
        category: Category for grouping (e.g., "Users", "Routing", "Analytics")
        requires_group: Whether utility requires a group selection
        requires_queue: Whether utility requires a queue selection
        requires_user: Whether utility requires a user selection
    """
    id: str
    name: str
    description: str
    icon: str = "ðŸ”§"
    category: str = "General"
    requires_group: bool = False
    requires_queue: bool = False
    requires_user: bool = False
    tags: List[str] = field(default_factory=list)


class BaseUtility(ABC):
    """
    Abstract base class for Genesys Cloud utilities.

    All utilities should inherit from this class and implement
    the required methods.

    Example:
        class MyUtility(BaseUtility):
            @staticmethod
            def get_config() -> UtilityConfig:
                return UtilityConfig(
                    id="my_utility",
                    name="My Utility",
                    description="Does something useful",
                    icon="ðŸ”§",
                    category="General"
                )

            def render_sidebar(self):
                # Add sidebar controls
                pass

            def render_main(self):
                # Render main content
                pass
    """

    def __init__(self, api):
        """
        Initialize utility with API client.

        Args:
            api: GenesysCloudAPI instance
        """
        self.api = api

    @staticmethod
    @abstractmethod
    def get_config() -> UtilityConfig:
        """
        Get utility configuration.

        Returns:
            UtilityConfig with utility metadata
        """
        pass

    @abstractmethod
    def render_sidebar(self) -> None:
        """
        Render sidebar controls for this utility.

        Called when this utility is active to add any
        utility-specific sidebar elements.
        """
        pass

    @abstractmethod
    def render_main(self) -> None:
        """
        Render main content area for this utility.

        Called when this utility is active to render
        the primary interface.
        """
        pass

    def init_state(self) -> None:
        """
        Initialize session state for this utility.

        Override to set up any utility-specific session state.
        Called once when utility is first loaded.
        """
        pass

    def cleanup(self) -> None:
        """
        Clean up when switching away from this utility.

        Override to clean up any resources or state.
        """
        pass

    # Helper methods for common operations

    def show_error(self, message: str) -> None:
        """Display error message."""
        st.error(message)

    def show_success(self, message: str) -> None:
        """Display success message."""
        st.success(message)

    def show_info(self, message: str) -> None:
        """Display info message."""
        st.info(message)

    def show_warning(self, message: str) -> None:
        """Display warning message."""
        st.warning(message)

    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get utility-specific state value.

        Args:
            key: State key (will be prefixed with utility id)
            default: Default value if not set

        Returns:
            State value
        """
        config = self.get_config()
        full_key = f"{config.id}_{key}"
        return st.session_state.get(full_key, default)

    def set_state(self, key: str, value: Any) -> None:
        """
        Set utility-specific state value.

        Args:
            key: State key (will be prefixed with utility id)
            value: Value to store
        """
        config = self.get_config()
        full_key = f"{config.id}_{key}"
        st.session_state[full_key] = value
