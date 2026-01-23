"""
Group Manager Utility
Manage group membership in Genesys Cloud.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional

from .base import BaseUtility, UtilityConfig


class GroupManagerUtility(BaseUtility):
    """
    Utility for managing Genesys Cloud group membership.

    Features:
    - View group members
    - Add members by email
    - Remove members
    - Export member lists
    - Import members from file
    """

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="group_manager",
            name="Group Manager",
            description="View and manage group membership",
            icon="👥",
            category="Users & Groups",
            requires_group=True,
            tags=["groups", "users", "membership", "bulk"]
        )

    def init_state(self) -> None:
        """Initialize utility state."""
        if self.get_state('page') is None:
            self.set_state('page', 'view')
        if self.get_state('group_id') is None:
            self.set_state('group_id', '')
        if self.get_state('group_info') is None:
            self.set_state('group_info', None)
        if self.get_state('members') is None:
            self.set_state('members', [])

    def render_sidebar(self) -> None:
        """Render sidebar controls."""
        st.markdown("#### Group Selection")

        # Group ID input
        group_id = st.text_input(
            "Group ID",
            value=self.get_state('group_id', ''),
            placeholder="Enter Group ID",
            key="gm_group_id_input"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Load", use_container_width=True, key="gm_load"):
                self._load_group(group_id)
        with col2:
            if st.button("Clear", use_container_width=True, key="gm_clear"):
                self._clear_group()

        # Show current group
        group_info = self.get_state('group_info')
        if group_info:
            st.caption(f"**{group_info.get('name')}**")
            members = self.get_state('members', [])
            st.caption(f"{len(members)} members")

        # Group search
        with st.expander("🔍 Search Groups"):
            query = st.text_input("Search", placeholder="Group name...", key="gm_search", label_visibility="collapsed")
            if query:
                groups = self.api.groups.search(query)
                for g in groups[:8]:
                    if st.button(g.get('name', 'Unknown'), key=f"gm_g_{g.get('id')}", use_container_width=True):
                        self._load_group(g.get('id'))

        st.markdown("---")

        # Operations
        st.markdown("#### Operations")

        group_loaded = self.get_state('group_info') is not None

        if st.button("📋 View Members", use_container_width=True, disabled=not group_loaded, key="gm_nav_view"):
            self.set_state('page', 'view')
            st.rerun()

        if st.button("➕ Add Members", use_container_width=True, disabled=not group_loaded, key="gm_nav_add"):
            self.set_state('page', 'add')
            st.rerun()

        if st.button("➖ Remove Members", use_container_width=True, disabled=not group_loaded, key="gm_nav_remove"):
            self.set_state('page', 'remove')
            st.rerun()

        if st.button("📤 Export", use_container_width=True, disabled=not group_loaded, key="gm_nav_export"):
            self.set_state('page', 'export')
            st.rerun()

    def render_main(self) -> None:
        """Render main content."""
        self.init_state()

        group_info = self.get_state('group_info')

        if not group_info:
            st.markdown("## Group Manager")
            st.info("Select a group from the sidebar to begin.")
            return

        page = self.get_state('page', 'view')

        if page == 'view':
            self._render_view_page()
        elif page == 'add':
            self._render_add_page()
        elif page == 'remove':
            self._render_remove_page()
        elif page == 'export':
            self._render_export_page()
        else:
            self._render_view_page()

    def _load_group(self, group_id: str) -> None:
        """Load a group by ID."""
        if not group_id:
            return

        with st.spinner("Loading group..."):
            response = self.api.groups.get(group_id)
            if response.success:
                self.set_state('group_id', group_id)
                self.set_state('group_info', response.data)
                members = self.api.groups.get_members(group_id)
                self.set_state('members', members)
                st.rerun()
            else:
                st.error(f"Failed to load group: {response.error}")

    def _clear_group(self) -> None:
        """Clear current group selection."""
        self.set_state('group_id', '')
        self.set_state('group_info', None)
        self.set_state('members', [])
        st.rerun()

    def _refresh_members(self) -> None:
        """Refresh member list."""
        group_id = self.get_state('group_id')
        if group_id:
            members = self.api.groups.get_members(group_id)
            self.set_state('members', members)

    def _render_view_page(self) -> None:
        """Render view members page."""
        group_info = self.get_state('group_info')
        members = self.get_state('members', [])

        st.markdown(f"## {group_info.get('name')}")
        st.caption(f"{len(members)} members")

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("🔄 Refresh"):
                self._refresh_members()
                st.rerun()

        # Filter
        search = st.text_input("Filter", placeholder="Search by name or email...")

        # Build dataframe
        df = pd.DataFrame([{
            'Name': m.get('name', 'Unknown'),
            'Email': m.get('email', 'N/A'),
            'ID': m.get('id', '')
        } for m in members])

        if search and not df.empty:
            mask = df['Name'].str.contains(search, case=False, na=False) | \
                   df['Email'].str.contains(search, case=False, na=False)
            df = df[mask]

        st.caption(f"Showing {len(df)} members")
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)

    def _render_add_page(self) -> None:
        """Render add members page."""
        group_info = self.get_state('group_info')

        st.markdown("## Add Members")
        st.caption(f"Group: **{group_info.get('name')}**")

        tab1, tab2 = st.tabs(["Paste Emails", "Upload File"])

        emails_input = ""

        with tab1:
            emails_input = st.text_area(
                "Enter emails (one per line)",
                height=200,
                placeholder="user1@example.com\nuser2@example.com",
                key="gm_emails_paste"
            )

        with tab2:
            uploaded = st.file_uploader("Upload CSV or TXT", type=['csv', 'txt'], key="gm_upload")
            if uploaded:
                content = uploaded.read().decode('utf-8')
                emails_input = "\n".join([
                    line.split(',')[0].strip().strip('"')
                    for line in content.split('\n')
                    if '@' in line
                ])
                st.text_area("Emails from file:", value=emails_input, height=150, disabled=True)

        col1, col2 = st.columns(2)
        with col1:
            dry_run = st.checkbox("Preview only", value=True, key="gm_dry_run")
        with col2:
            if st.button("Process", type="primary", use_container_width=True, key="gm_process"):
                if emails_input:
                    self._process_add(emails_input, dry_run)

    def _process_add(self, emails_input: str, dry_run: bool) -> None:
        """Process adding members."""
        emails = list(dict.fromkeys([
            e.strip() for e in emails_input.split('\n')
            if e.strip() and '@' in e
        ]))

        if not emails:
            st.error("No valid emails found")
            return

        st.markdown("### Processing")

        progress = st.progress(0)
        found = []
        not_found = []

        for i, email in enumerate(emails):
            progress.progress((i + 1) / len(emails))
            user = self.api.users.search_by_email(email)
            if user:
                found.append({'id': user['id'], 'name': user.get('name', 'Unknown'), 'email': email})
            else:
                not_found.append(email)

        col1, col2 = st.columns(2)

        with col1:
            st.success(f"**Found:** {len(found)}")
            for u in found:
                st.caption(f"✓ {u['email']}")

        with col2:
            if not_found:
                st.error(f"**Not found:** {len(not_found)}")
                for e in not_found:
                    st.caption(f"✗ {e}")

        if found and not dry_run:
            st.markdown("---")
            group_id = self.get_state('group_id')
            member_ids = [u['id'] for u in found]
            response = self.api.groups.add_members(group_id, member_ids)
            if response.success:
                st.success(f"Added {len(found)} members")
                self._refresh_members()
            else:
                st.error(response.error)
        elif found and dry_run:
            st.info("Preview complete. Uncheck 'Preview only' to add members.")

    def _render_remove_page(self) -> None:
        """Render remove members page."""
        group_info = self.get_state('group_info')
        members = self.get_state('members', [])

        st.markdown("## Remove Members")
        st.caption(f"Group: **{group_info.get('name')}** · {len(members)} members")

        search = st.text_input("Filter", placeholder="Search...", key="gm_remove_filter")

        filtered = members
        if search:
            filtered = [
                m for m in members
                if search.lower() in m.get('name', '').lower() or
                   search.lower() in m.get('email', '').lower()
            ]

        options = {f"{m.get('name')} ({m.get('email')})": m.get('id') for m in filtered}

        selected = st.multiselect("Select members to remove", options=list(options.keys()), key="gm_remove_select")

        if selected:
            st.warning(f"⚠️ {len(selected)} member(s) selected")

            confirm = st.checkbox("I confirm removal", key="gm_remove_confirm")

            if st.button("Remove", type="primary", disabled=not confirm, key="gm_remove_btn"):
                member_ids = [options[s] for s in selected]
                response = self.api.groups.remove_members(self.get_state('group_id'), member_ids)
                if response.success:
                    st.success(f"Removed {len(selected)} members")
                    self._refresh_members()
                    st.rerun()
                else:
                    st.error(response.error)

    def _render_export_page(self) -> None:
        """Render export page."""
        group_info = self.get_state('group_info')
        members = self.get_state('members', [])

        st.markdown("## Export Members")
        st.caption(f"Group: **{group_info.get('name')}** · {len(members)} members")

        df = pd.DataFrame([{
            'Name': m.get('name', 'Unknown'),
            'Email': m.get('email', 'N/A'),
            'ID': m.get('id', '')
        } for m in members])

        st.markdown("### Download Options")

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "📥 CSV (Full)",
                data=df.to_csv(index=False),
                file_name=f"{group_info.get('name', 'group')}_members.csv",
                mime="text/csv",
                use_container_width=True,
                key="gm_export_csv"
            )

        with col2:
            emails = "\n".join(df['Email'].dropna().tolist())
            st.download_button(
                "📥 Emails Only",
                data=emails,
                file_name=f"{group_info.get('name', 'group')}_emails.txt",
                mime="text/plain",
                use_container_width=True,
                key="gm_export_emails"
            )

        st.markdown("### Preview")
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)
