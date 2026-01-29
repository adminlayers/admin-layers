#!/usr/bin/env python3
"""
Admin Layers - Genesys Cloud Utilities Suite
Modular utilities for Genesys Cloud administration.
Supports hosted deployment on Streamlit Community Cloud with encrypted storage.
"""

from typing import Dict, Type

import streamlit as st

from core.demo import DemoAPI, is_demo_mode, set_demo_mode
from core.diagnostics import (
    cache_report,
    clear_cached_report,
    get_cached_report,
    render_diagnostics_summary,
    run_diagnostics,
)
from core.encrypted_storage import get_storage
from core.services import validate_backend

# Core modules
from genesys_cloud import GenesysAuth, GenesysCloudAPI, get_regions, load_config

# Utilities
from utilities import (
    BaseUtility,
    ChatAssistantUtility,
    GroupManagerUtility,
    QueueManagerUtility,
    SkillManagerUtility,
    UserManagerUtility,
)

# =============================================================================
# Configuration
# =============================================================================

APP_NAME = "Admin Layers"
APP_VERSION = "1.3.0"

# Register available utilities here
UTILITIES: Dict[str, Type[BaseUtility]] = {
    "chat_assistant": ChatAssistantUtility,
    "group_manager": GroupManagerUtility,
    "user_manager": UserManagerUtility,
    "skill_manager": SkillManagerUtility,
    "queue_manager": QueueManagerUtility,
}

# =============================================================================
# Page Config
# =============================================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# Styles
# =============================================================================

st.markdown(
    """
<style>
    /* ===============================================================
       Admin Layers – Global Styles
       =============================================================== */

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ---------------------------------------------------------------
       GLOBAL: Hide ALL Material Symbols icon-text
       ---------------------------------------------------------------
       Streamlit uses the "Material Symbols Rounded" web font for UI
       icons. The font is applied via inline font-family (not a CSS
       class). Icons render as <span data-testid="stIconMaterial">
       with text content like "keyboard_double_arrow_right".

       When the web font fails to load (common on mobile), the raw
       icon names render as visible text throughout the UI.

       We collapse ALL such elements. The app uses emoji for
       navigation, which don't depend on the web font.
       --------------------------------------------------------------- */
    [data-testid="stIconMaterial"] {
        font-size: 0 !important;
        color: transparent !important;
        -webkit-text-fill-color: transparent !important;
        width: 0 !important;
        height: 0 !important;
        max-width: 0 !important;
        max-height: 0 !important;
        overflow: hidden !important;
        display: inline-block !important;
        line-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* ---------------------------------------------------------------
       Sidebar toggle buttons
       ---------------------------------------------------------------
       With icon text hidden, the toggle buttons collapse to zero.
       We restore their dimensions and add CSS replacement icons.

       Streamlit 1.38+ uses: data-testid="stSidebarCollapseButton"
       Streamlit <1.38 uses:  data-testid="collapsedControl"
       --------------------------------------------------------------- */

    /* Collapse button (close sidebar) – Streamlit 1.38+ */
    [data-testid="stSidebarCollapseButton"] {
        position: relative !important;
        min-width: 2.75rem !important;
        min-height: 2.75rem !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebarCollapseButton"] button {
        position: relative !important;
        width: 2.75rem !important;
        height: 2.75rem !important;
        min-width: 2.75rem !important;
        overflow: hidden !important;
        background: rgba(15, 23, 42, 0.9) !important;
        border-radius: 0.5rem !important;
        padding: 0 !important;
    }
    [data-testid="stSidebarCollapseButton"] button::after {
        content: "\2715";
        position: absolute;
        inset: 0;
        display: flex !important;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem !important;
        color: #e2e8f0 !important;
        pointer-events: none;
    }

    /* Collapse button – Streamlit <1.38 (backward compat) */
    [data-testid="collapsedControl"] {
        position: relative !important;
        width: 2.75rem !important;
        height: 2.75rem !important;
        min-width: 2.75rem !important;
        max-width: 2.75rem !important;
        overflow: hidden !important;
        background: rgba(15, 23, 42, 0.9) !important;
        border-radius: 0.5rem;
        padding: 0 !important;
        z-index: 1100 !important;
    }
    [data-testid="collapsedControl"] * {
        visibility: hidden !important;
        font-size: 0 !important;
        overflow: hidden !important;
    }
    [data-testid="collapsedControl"]::after {
        content: "\2630";
        position: absolute;
        inset: 0;
        display: flex !important;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem !important;
        color: #e2e8f0 !important;
        visibility: visible !important;
        pointer-events: none;
    }

    /* Expand button (open sidebar) – uses :has() to target
       any button in the header that contains a hidden icon */
    [data-testid="stHeader"] button:has([data-testid="stIconMaterial"]) {
        position: relative !important;
        width: 2.75rem !important;
        height: 2.75rem !important;
        min-width: 2.75rem !important;
        min-height: 2.75rem !important;
        overflow: hidden !important;
        background: rgba(15, 23, 42, 0.9) !important;
        border-radius: 0.5rem !important;
        padding: 0 !important;
    }
    [data-testid="stHeader"] button:has([data-testid="stIconMaterial"])::after {
        content: "\2630";
        position: absolute;
        inset: 0;
        display: flex !important;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem !important;
        color: #e2e8f0 !important;
        pointer-events: none;
    }

    /* Fallback: expand button inside collapsed sidebar */
    [data-testid="stSidebar"][aria-expanded="false"] button:has([data-testid="stIconMaterial"]) {
        position: relative !important;
        width: 2.75rem !important;
        height: 2.75rem !important;
        min-width: 2.75rem !important;
        min-height: 2.75rem !important;
        overflow: hidden !important;
        background: rgba(15, 23, 42, 0.9) !important;
        border-radius: 0.5rem !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"][aria-expanded="false"] button:has([data-testid="stIconMaterial"])::after {
        content: "\2630";
        position: absolute;
        inset: 0;
        display: flex !important;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem !important;
        color: #e2e8f0 !important;
        pointer-events: none;
    }

    /* ---------------------------------------------------------------
       Sidebar chrome
       --------------------------------------------------------------- */
    [data-testid="stSidebar"] {
        background-color: #1a2632 !important;
    }

    /* Ensure sidebar content has adequate padding (prevents left-clip) */
    [data-testid="stSidebarContent"] {
        padding-left: 1.25rem !important;
        padding-right: 0.75rem !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding-left: 1.25rem !important;
        padding-right: 0.75rem !important;
    }

    [data-testid="stSidebar"] button {
        padding: 0.4rem 0.5rem;
        font-size: 0.82rem;
        border-radius: 6px;
        line-height: 1.2;
    }

    [data-testid="stSidebar"] .stButton + .stButton {
        margin-top: 0.2rem;
    }

    [data-testid="stSidebar"] hr {
        margin: 0.4rem 0;
    }

    /* ---------------------------------------------------------------
       Component styles
       --------------------------------------------------------------- */
    .nav-header {
        font-size: 0.7rem;
        font-weight: 600;
        color: #8899aa;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin: 0.8rem 0 0.3rem 0;
    }

    .status-badge {
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 500;
        display: inline-block;
    }
    .status-connected {
        background: #1e3a2f;
        color: #4ade80;
        border: 1px solid #2d5a3f;
    }
    .status-demo {
        background: #3a2e1e;
        color: #fbbf24;
        border: 1px solid #5a4a2d;
    }
    .status-disconnected {
        background: #3a1e1e;
        color: #f87171;
        border: 1px solid #5a2d2d;
    }

    .demo-banner {
        background: linear-gradient(135deg, #2d1f0e 0%, #3a2e1e 100%);
        border: 1px solid #5a4a2d;
        border-radius: 6px;
        padding: 8px 16px;
        margin-bottom: 16px;
        color: #fbbf24;
        font-size: 0.85rem;
    }

    .info-row {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        padding: 0.5rem 0;
        font-size: 0.9rem;
    }
    .info-row .info-item { color: #ccc; }
    .info-row .info-label {
        color: #8899aa;
        font-size: 0.75rem;
        text-transform: uppercase;
    }
    .info-row .info-value { font-weight: 600; }

    .storage-info {
        font-size: 0.75rem;
        color: #8899aa;
        padding: 4px 0;
    }

    /* ---------------------------------------------------------------
       Mobile refinements  (max-width: 768px)
       We do NOT override sidebar positioning – Streamlit handles
       the overlay/slide natively. We only adjust spacing and
       touch targets.
       --------------------------------------------------------------- */
    @media (max-width: 768px) {
        .block-container {
            padding: 3rem 0.75rem 2rem !important;
        }

        [data-testid="stSidebar"] button {
            padding: 0.5rem 0.6rem;
            font-size: 0.85rem;
            min-height: 2.5rem;
        }

        [data-testid="stSidebar"] .stButton + .stButton {
            margin-top: 0.3rem;
        }

        [data-testid="stHorizontalBlock"] {
            gap: 0.3rem;
        }

        [data-testid="stSidebar"] {
            overflow-x: hidden !important;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)

# =============================================================================
# Session State
# =============================================================================


def init_session_state():
    """Initialize global session state."""
    defaults = {
        "authenticated": False,
        "auth": None,
        "api": None,
        "current_utility": None,
        "page": "home",
        "demo_mode": False,
        "local_user": None,
        "active_profile_id": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # Load active profile from storage
    if st.session_state.local_user is None:
        storage = get_storage()
        # Try new multi-profile system first
        active_profile = storage.get_active_profile()
        if active_profile:
            st.session_state.local_user = active_profile
            st.session_state.active_profile_id = active_profile.get("id")
        else:
            # Fall back to legacy single profile
            st.session_state.local_user = storage.retrieve_local_user()


def _run_startup_diagnostics(api, is_demo: bool = False):
    """Run diagnostics after authentication and cache the report."""
    # Validate backend interface
    errors = validate_backend(api)
    if errors:
        st.warning(f"Backend missing methods: {', '.join(errors[:5])}")

    # Run endpoint checks
    report = run_diagnostics(api, is_demo=is_demo)
    cache_report(report)
    return report


def try_auto_auth():
    """Attempt auto-authentication from environment or encrypted storage."""
    if st.session_state.authenticated:
        return

    # Try environment variables / config file first
    auth = GenesysAuth.from_config()
    if auth:
        success, _ = auth.authenticate()
        if success:
            st.session_state.authenticated = True
            st.session_state.auth = auth
            st.session_state.api = GenesysCloudAPI(auth)
            _run_startup_diagnostics(st.session_state.api, is_demo=False)
            return

    # Try encrypted storage
    storage = get_storage()
    creds = storage.retrieve_credentials()
    if creds:
        auth = GenesysAuth.from_credentials(
            creds["client_id"],
            creds["client_secret"],
            creds.get("region", "mypurecloud.com"),
        )
        success, _ = auth.authenticate()
        if success:
            st.session_state.authenticated = True
            st.session_state.auth = auth
            st.session_state.api = GenesysCloudAPI(auth)
            _run_startup_diagnostics(st.session_state.api, is_demo=False)


def activate_demo_mode():
    """Activate demo mode with mock API."""
    set_demo_mode(True)
    st.session_state.authenticated = True
    st.session_state.auth = None
    st.session_state.api = DemoAPI()
    # Skip diagnostics in demo mode – demo always returns OK which is misleading


def deactivate_session():
    """Clear all session and auth state."""
    set_demo_mode(False)
    st.session_state.authenticated = False
    st.session_state.auth = None
    st.session_state.api = None
    st.session_state.current_utility = None
    st.session_state.page = "home"
    clear_cached_report()


# =============================================================================
# Sidebar
# =============================================================================


def render_sidebar():
    """Render main sidebar."""
    with st.sidebar:
        st.markdown(f"### ⚙️ {APP_NAME}")
        if st.session_state.local_user:
            name = st.session_state.local_user.get("name", "Local User")
            st.caption(f"Signed in as **{name}**")

        # Connection status
        if is_demo_mode():
            st.markdown(
                '<span class="status-badge status-demo">◉ Demo Mode</span>',
                unsafe_allow_html=True,
            )
        elif st.session_state.authenticated:
            st.markdown(
                '<span class="status-badge status-connected">◉ Connected</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="status-badge status-disconnected">◉ Disconnected</span>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Navigation
        st.markdown('<p class="nav-header">Navigation</p>', unsafe_allow_html=True)

        if st.button("🏠 Home", use_container_width=True, key="nav_home"):
            st.session_state.page = "home"
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
                if st.button(
                    f"{config.icon} {config.name}",
                    use_container_width=True,
                    key=f"nav_{util_id}",
                    disabled=not st.session_state.authenticated,
                ):
                    st.session_state.current_utility = util_id
                    st.session_state.page = "utility"
                    st.rerun()

        st.markdown("---")

        # Settings
        st.markdown('<p class="nav-header">Settings</p>', unsafe_allow_html=True)

        if st.session_state.authenticated:
            if is_demo_mode():
                st.caption("Mode: Demo (sample data)")
            else:
                region = (
                    st.session_state.auth.config.region
                    if st.session_state.auth
                    else "Unknown"
                )
                st.caption(f"Region: {region}")

            if st.button(
                "🔓 Disconnect", use_container_width=True, key="nav_disconnect"
            ):
                deactivate_session()
                st.rerun()
        else:
            if st.button("🔑 Connect", use_container_width=True, key="nav_connect"):
                st.session_state.page = "connect"
                st.rerun()

        # Storage info
        if st.button("🔒 Storage Info", use_container_width=True, key="nav_storage"):
            st.session_state.page = "storage_info"
            st.session_state.current_utility = None
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
    # Demo mode banner
    if is_demo_mode():
        st.markdown(
            '<div class="demo-banner">'
            "⚡ <strong>Demo Mode</strong> — "
            "Exploring with sample data. No real Genesys Cloud connection. "
            "Connect with real credentials to manage your org."
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown(f"## Welcome to Admin Layers")
    st.caption(f"v{APP_VERSION}")

    if not st.session_state.authenticated:
        st.markdown(
            "Bulk administration tools for Genesys Cloud. "
            "Connect with your credentials or try demo mode."
        )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Connect to Your Org")
            st.markdown(
                "Use your Genesys Cloud OAuth credentials "
                "to manage groups, skills, and queues."
            )
            if st.button("🔑 Connect", use_container_width=True, key="home_connect"):
                st.session_state.page = "connect"
                st.rerun()

        with col2:
            st.markdown("#### Try Demo Mode")
            st.markdown(
                "Explore the interface with sample data. " "No credentials required."
            )
            if st.button("⚡ Launch Demo", use_container_width=True, key="home_demo"):
                activate_demo_mode()
                st.rerun()

        st.markdown("---")

        with st.expander("About this application"):
            st.markdown(f"""
**{APP_NAME}** provides modular utilities for managing
Genesys Cloud resources with bulk operations, dry-run previews,
and encrypted local storage.

**Available Utilities:**
            """)

            for util_id, util_class in UTILITIES.items():
                config = util_class.get_config()
                st.markdown(f"- {config.icon} **{config.name}**: {config.description}")

            st.markdown("""
**Security:**
- All credentials are encrypted at rest (AES-128-CBC + HMAC-SHA256)
- Direct API calls to Genesys Cloud (no proxy)
- No data passes through third-party servers
- Full audit trail stored locally
            """)

        return

    st.markdown("Select a utility from the sidebar to begin.")

    # Diagnostics summary – only show for live API connections
    if not is_demo_mode():
        report = get_cached_report()
        if report:
            render_diagnostics_summary(report)
        else:
            if st.session_state.api:
                with st.spinner("Running endpoint diagnostics..."):
                    report = _run_startup_diagnostics(
                        st.session_state.api, is_demo=False
                    )
                render_diagnostics_summary(report)

        c_diag, _ = st.columns([1, 3])
        with c_diag:
            if st.button("Re-run Diagnostics", key="home_rerun_diag"):
                if st.session_state.api:
                    with st.spinner("Running diagnostics..."):
                        report = _run_startup_diagnostics(
                            st.session_state.api, is_demo=False
                        )
                    st.rerun()

    st.markdown("---")

    # Show utility cards
    st.markdown("### Available Utilities")

    cols = st.columns(2)

    for i, (util_id, util_class) in enumerate(UTILITIES.items()):
        config = util_class.get_config()

        with cols[i % 2]:
            with st.container():
                st.markdown(f"#### {config.icon} {config.name}")
                st.caption(config.description)
                st.caption(f"Category: {config.category}")

                if st.button("Open", key=f"open_{util_id}", use_container_width=True):
                    st.session_state.current_utility = util_id
                    st.session_state.page = "utility"
                    st.rerun()


def page_connect():
    """Connection page."""
    st.markdown("## Connect to Genesys Cloud")

    tab1, tab2 = st.tabs(["🔑 Credentials", "⚡ Demo Mode"])

    with tab1:
        config = load_config()

        # Check encrypted storage for saved credentials
        storage = get_storage()
        saved_creds = storage.retrieve_credentials()
        saved_profile = storage.retrieve_local_user()

        with st.expander("User Profiles (multiple login identities)", expanded=False):
            st.markdown(
                "Create multiple profiles for different identities. "
                "Profiles are stored locally in encrypted storage."
            )

            # List existing profiles
            profiles = storage.retrieve_profiles()
            active_id = st.session_state.active_profile_id

            if profiles:
                st.markdown("**Your Profiles:**")
                for profile in profiles:
                    pid = profile.get("id", "")
                    pname = profile.get("name", "Unknown")
                    pemail = profile.get("email", "")
                    is_active = pid == active_id

                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        label = f"**{pname}** ({pemail})"
                        if is_active:
                            label += " ✓"
                        st.markdown(label)
                    with col2:
                        if not is_active:
                            if st.button("Use", key=f"use_profile_{pid}"):
                                storage.set_active_profile(pid)
                                st.session_state.local_user = profile
                                st.session_state.active_profile_id = pid
                                st.rerun()
                    with col3:
                        if st.button("🗑️", key=f"del_profile_{pid}"):
                            storage.delete_profile(pid)
                            if is_active:
                                st.session_state.local_user = None
                                st.session_state.active_profile_id = None
                            st.rerun()

                st.markdown("---")

            # Add new profile form
            st.markdown("**Add New Profile:**")
            with st.form("add_profile_form"):
                name = st.text_input(
                    "Display name",
                    placeholder="Jane Admin",
                )
                email = st.text_input(
                    "Work email",
                    placeholder="jane@company.com",
                )
                company = st.text_input(
                    "Company",
                    placeholder="Company name (optional)",
                )
                if st.form_submit_button("Add Profile", use_container_width=True):
                    if name and email:
                        new_id = storage.add_profile(
                            {
                                "name": name,
                                "email": email,
                                "company": company,
                            }
                        )
                        # Auto-activate if first profile
                        if len(profiles) == 0:
                            storage.set_active_profile(new_id)
                            new_profile = storage.get_profile(new_id)
                            st.session_state.local_user = new_profile
                            st.session_state.active_profile_id = new_id
                        st.success(f"Profile '{name}' added!")
                        st.rerun()
                    else:
                        st.error("Name and email are required.")

        with st.form("connect_form"):
            st.markdown("### OAuth Client Credentials")
            client_id = st.text_input(
                "Client ID",
                value=(saved_creds or {}).get("client_id", "")
                or (config.client_id if config else ""),
                type="password",
            )

            client_secret = st.text_input(
                "Client Secret",
                value=(saved_creds or {}).get("client_secret", "")
                or (config.client_secret if config else ""),
                type="password",
            )

            regions = get_regions()
            default_region = (saved_creds or {}).get("region") or (
                config.region if config else "mypurecloud.com"
            )
            idx = regions.index(default_region) if default_region in regions else 0
            region = st.selectbox("Region", regions, index=idx)

            remember = st.checkbox(
                "Remember credentials (encrypted)",
                value=saved_creds is not None,
                help="Credentials are encrypted using AES-128-CBC with HMAC-SHA256",
            )

            if st.form_submit_button("Connect", use_container_width=True):
                if client_id and client_secret:
                    auth = GenesysAuth.from_credentials(
                        client_id, client_secret, region
                    )
                    success, message = auth.authenticate()

                    if success:
                        if remember:
                            storage.store_credentials(client_id, client_secret, region)
                        else:
                            storage.clear_credentials()

                        set_demo_mode(False)
                        st.session_state.authenticated = True
                        st.session_state.auth = auth
                        st.session_state.api = GenesysCloudAPI(auth)
                        _run_startup_diagnostics(st.session_state.api, is_demo=False)
                        st.session_state.page = "home"
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Enter Client ID and Client Secret")

        if saved_creds:
            if st.button("🗑️ Clear Saved Credentials", key="clear_saved"):
                storage.clear_credentials()
                st.success("Saved credentials cleared")
                st.rerun()

    with tab2:
        st.markdown("### Demo Mode")
        st.markdown(
            "Explore Admin Layers with realistic sample data. "
            "No Genesys Cloud credentials required."
        )

        st.markdown("""
**Demo includes:**
- 30 sample users across Support, Sales, Engineering, QA, and HR
- 5 groups (Tier 1 Support, Tier 2 Support, Sales Team, All Hands, Weekend Coverage)
- 5 queues (General Support, Billing, Sales Inbound, Technical, VIP)
- 12 routing skills with user assignments
        """)

        st.info(
            "Demo mode uses simulated data. No API calls are made. "
            "All operations (add/remove) succeed without side effects."
        )

        if st.button(
            "⚡ Launch Demo Mode",
            type="primary",
            use_container_width=True,
            key="connect_demo",
        ):
            activate_demo_mode()
            st.rerun()


def page_utility():
    """Utility page."""
    # Demo mode banner
    if is_demo_mode():
        st.markdown(
            '<div class="demo-banner">'
            "⚡ <strong>Demo Mode</strong> — Sample data only"
            "</div>",
            unsafe_allow_html=True,
        )

    util_id = st.session_state.current_utility

    if not util_id or util_id not in UTILITIES:
        st.session_state.page = "home"
        st.rerun()
        return

    util_class = UTILITIES[util_id]
    utility = util_class(st.session_state.api)
    utility.render_main()


def page_storage_info():
    """Storage information page."""
    st.markdown("## Storage & Security")

    storage = get_storage()
    info = storage.get_storage_info()

    st.markdown("### Encryption")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Algorithm:**")
        st.markdown("**Key Source:**")
        st.markdown("**Persistent:**")
    with col2:
        st.markdown(info["encryption"])
        st.markdown(info["key_source"])
        st.markdown("Yes" if info["persistent"] else "No (session only)")

    st.markdown("### Storage Backend")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Backend:**")
        if info["storage_dir"]:
            st.markdown("**Location:**")
    with col2:
        st.markdown(info["backend"])
        if info["storage_dir"]:
            st.markdown(f"`{info['storage_dir']}`")

    st.markdown("---")

    st.markdown("### How It Works")
    st.markdown("""
**Credential Storage:**
- Credentials are encrypted using Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256)
- Encrypted data stored locally on disk when available, otherwise in session state
- Encryption key sourced from `st.secrets`, environment variable, or auto-generated per session

**Session Data:**
- Session state managed by Streamlit's built-in session management
- Each browser tab gets an isolated session
- Session data is cleared when the tab closes

**Action History:**
- All operations logged locally in encrypted storage
- History retained for audit and rollback purposes
- Maximum 500 records maintained

**Local User Profile:**
- Optional profile stored locally for SaaS-style deployments
- Encrypted at rest alongside credentials
- Used to label actions and sessions

**Hosted Deployment (Streamlit Community Cloud):**
- Set `encryption_key` in Streamlit Secrets for persistent encrypted storage
- Credentials entered through the UI are encrypted in session state
- No credentials or data are transmitted to third parties
    """)

    st.markdown("---")

    # Saved credentials management
    st.markdown("### Saved Data")

    creds = storage.retrieve_credentials()
    if creds:
        st.success("Encrypted credentials found")
        st.caption(f"Stored at: {creds.get('stored_at', 'Unknown')}")
        st.caption(f"Region: {creds.get('region', 'Unknown')}")

        if st.button("🗑️ Clear Saved Credentials", key="storage_clear_creds"):
            storage.clear_credentials()
            st.success("Credentials cleared")
            st.rerun()
    else:
        st.info("No saved credentials")

    st.markdown("### Local User Profile")
    profile = storage.retrieve_local_user()
    if profile:
        st.success("Local profile saved")
        st.caption(f"Name: {profile.get('name', 'Unknown')}")
        st.caption(f"Email: {profile.get('email', 'Unknown')}")
        if profile.get("company"):
            st.caption(f"Company: {profile.get('company')}")
        if st.button("🗑️ Clear Local Profile", key="storage_clear_profile"):
            storage.clear_local_user()
            st.session_state.local_user = None
            st.success("Local profile cleared")
            st.rerun()
    else:
        st.info("No local profile saved")


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

    if page == "home":
        page_home()
    elif page == "connect":
        page_connect()
    elif page == "utility":
        page_utility()
    elif page == "storage_info":
        page_storage_info()
    else:
        page_home()


if __name__ == "__main__":
    main()
