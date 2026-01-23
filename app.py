#!/usr/bin/env python3
"""
Genesys Cloud Utilities Suite
Modular utilities for Genesys Cloud administration.
"""

import streamlit as st
from typing import Dict, Type

# Core modules
from genesys_cloud import GenesysAuth, GenesysCloudAPI, load_config, get_regions

# Utilities
from utilities import BaseUtility, GroupManagerUtility, SkillManagerUtility, QueueManagerUtility

# =============================================================================
# Configuration
# =============================================================================

APP_NAME = "Genesys Cloud Utilities"
APP_VERSION = "1.0.0"

# Register available utilities here
UTILITIES: Dict[str, Type[BaseUtility]] = {
    "group_manager": GroupManagerUtility,
    "skill_manager": SkillManagerUtility,
    "queue_manager": QueueManagerUtility,
    # Add more utilities as they're created:
    # "user_manager": UserManagerUtility,
    # "conversation_tools": ConversationToolsUtility,
}

# =============================================================================
# Page Config
# =============================================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="âš™ï¸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# Styles
# =============================================================================

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
    }

    .nav-header {
        font-size: 0.7rem;
        font-weight: 600;
        color: #6C757D;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 1.25rem 0 0.5rem 0;
    }

    .status-badge {
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 500;
    }

    .status-connected {
        background: #D4EDDA;
        color: #155724;
    }

    .status-disconnected {
        background: #F8D7DA;
        color: #721C24;
    }

    .utility-card {
        border: 1px solid #DEE2E6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #FFFFFF;
    }

    .utility-card:hover {
        border-color: #4A6FA5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Session State
# =============================================================================

def init_session_state():
    """Initialize global session state."""
    defaults = {
        'authenticated': False,
        'auth': None,
        'api': None,
        'current_utility': None,
        'page': 'home'
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def try_auto_auth():
    """Attempt auto-authentication from environment."""
    if st.session_state.authenticated:
        return

    auth = GenesysAuth.from_config()
    if auth:
        success, _ = auth.authenticate()
        if success:
            st.session_state.authenticated = True
            st.session_state.auth = auth
            st.session_state.api = GenesysCloudAPI(auth)


# =============================================================================
# Sidebar
# =============================================================================

def render_sidebar():
    """Render main sidebar."""
    with st.sidebar:
        st.markdown(f"### âš™ï¸ {APP_NAME}")

        # Connection status
        if st.session_state.authenticated:
            st.markdown('<span class="status-badge status-connected">â— Connected</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge status-disconnected">â— Disconnected</span>', unsafe_allow_html=True)

        st.markdown("---")

        # Navigation
        st.markdown('<p class="nav-header">Navigation</p>', unsafe_allow_html=True)

        if st.button("ðŸ  Home", use_container_width=True, key="nav_home"):
            st.session_state.page = 'home'
            st.session_state.current_utility = None
            st.rerun()

        st.markdown("---")

        # Utilities section
        st.markdown('<p class="nav-header">Utilities</p>', unsafe_allow_html=True)

        # Group by category
        categories: Dict[str, list] = {}
        for util_id, util_class in UTILITIES.items():
            config = util_class.get_config()
            cat = config.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((util_id, util_class, config))

        for category, utils in sorted(categories.items()):
            for util_id, util_class, config in utils:
                is_active = st.session_state.current_utility == util_id
                btn_type = "primary" if is_active else "secondary"

                if st.button(
                    f"{config.icon} {config.name}",
                    use_container_width=True,
                    key=f"nav_{util_id}",
                    disabled=not st.session_state.authenticated
                ):
                    st.session_state.current_utility = util_id
                    st.session_state.page = 'utility'
                    st.rerun()

        st.markdown("---")

        # Settings
        st.markdown('<p class="nav-header">Settings</p>', unsafe_allow_html=True)

        if st.session_state.authenticated:
            region = st.session_state.auth.config.region if st.session_state.auth else "Unknown"
            st.caption(f"Region: {region}")

            if st.button("ðŸ”“ Disconnect", use_container_width=True, key="nav_disconnect"):
                st.session_state.authenticated = False
                st.session_state.auth = None
                st.session_state.api = None
                st.session_state.current_utility = None
                st.rerun()
        else:
            if st.button("ðŸ”‘ Connect", use_container_width=True, key="nav_connect"):
                st.session_state.page = 'connect'
                st.rerun()

        # Version
        st.markdown("---")
        st.caption(f"v{APP_VERSION}")


def render_utility_sidebar():
    """Render utility-specific sidebar controls."""
    util_id = st.session_state.current_utility
    if not util_id or util_id not in UTILITIES:
        return

    util_class = UTILITIES[util_id]
    utility = util_class(st.session_state.api)

    with st.sidebar:
        st.markdown("---")
        config = util_class.get_config()
        st.markdown(f'<p class="nav-header">{config.name}</p>', unsafe_allow_html=True)
        utility.render_sidebar()


# =============================================================================
# Pages
# =============================================================================

def page_home():
    """Home page."""
    st.markdown("## Welcome")

    if not st.session_state.authenticated:
        st.warning("Connect to Genesys Cloud to get started.")

        with st.expander("About this application"):
            st.markdown(f"""
            **{APP_NAME}** provides a collection of utilities for managing
            Genesys Cloud resources.

            **Available Utilities:**
            """)

            for util_id, util_class in UTILITIES.items():
                config = util_class.get_config()
                st.markdown(f"- {config.icon} **{config.name}**: {config.description}")

        return

    st.markdown("Select a utility from the sidebar to begin.")

    # Show utility cards
    st.markdown("### Available Utilities")

    cols = st.columns(3)

    for i, (util_id, util_class) in enumerate(UTILITIES.items()):
        config = util_class.get_config()

        with cols[i % 3]:
            with st.container():
                st.markdown(f"#### {config.icon} {config.name}")
                st.caption(config.description)
                st.caption(f"Category: {config.category}")

                if st.button("Open", key=f"open_{util_id}", use_container_width=True):
                    st.session_state.current_utility = util_id
                    st.session_state.page = 'utility'
                    st.rerun()


def page_connect():
    """Connection page."""
    st.markdown("## Connect to Genesys Cloud")

    config = load_config()

    with st.form("connect_form"):
        client_id = st.text_input(
            "Client ID",
            value=config.client_id if config else '',
            type="password"
        )

        client_secret = st.text_input(
            "Client Secret",
            value=config.client_secret if config else '',
            type="password"
        )

        regions = get_regions()
        default_region = config.region if config else 'mypurecloud.com'
        idx = regions.index(default_region) if default_region in regions else 0
        region = st.selectbox("Region", regions, index=idx)

        if st.form_submit_button("Connect", use_container_width=True):
            if client_id and client_secret:
                auth = GenesysAuth.from_credentials(client_id, client_secret, region)
                success, message = auth.authenticate()

                if success:
                    st.session_state.authenticated = True
                    st.session_state.auth = auth
                    st.session_state.api = GenesysCloudAPI(auth)
                    st.session_state.page = 'home'
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Enter Client ID and Client Secret")


def page_utility():
    """Utility page."""
    util_id = st.session_state.current_utility

    if not util_id or util_id not in UTILITIES:
        st.session_state.page = 'home'
        st.rerun()
        return

    util_class = UTILITIES[util_id]
    utility = util_class(st.session_state.api)
    utility.render_main()


# =============================================================================
# Main
# =============================================================================

def main():
    init_session_state()
    try_auto_auth()

    # Main sidebar
    render_sidebar()

    # Utility sidebar (if active)
    if st.session_state.current_utility:
        render_utility_sidebar()

    # Route to page
    page = st.session_state.page

    if page == 'home':
        page_home()
    elif page == 'connect':
        page_connect()
    elif page == 'utility':
        page_utility()
    else:
        page_home()


if __name__ == "__main__":
    main()
