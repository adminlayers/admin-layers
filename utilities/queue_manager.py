"""
Queue Manager Utility
Manage queue membership in Genesys Cloud.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional

from .base import BaseUtility, UtilityConfig


class QueueManagerUtility(BaseUtility):
    """
    Utility for managing Genesys Cloud queue membership.

    Features:
    - View queue members
    - Search queues
    - View queue configuration
    - Export queue data
    """

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="queue_manager",
            name="Queue Manager",
            description="View and manage queue membership",
            icon="📞",
            category="Routing",
            requires_queue=True,
            tags=["queues", "routing", "membership", "agents"]
        )

    def init_state(self) -> None:
        """Initialize utility state."""
        if self.get_state('page') is None:
            self.set_state('page', 'view')
        if self.get_state('queue_id') is None:
            self.set_state('queue_id', '')
        if self.get_state('queue_info') is None:
            self.set_state('queue_info', None)
        if self.get_state('members') is None:
            self.set_state('members', [])

    def render_sidebar(self) -> None:
        """Render sidebar controls."""
        st.markdown("#### Queue Selection")

        # Queue ID input
        queue_id = st.text_input(
            "Queue ID",
            value=self.get_state('queue_id', ''),
            placeholder="Enter Queue ID",
            key="qm_queue_id_input"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Load", use_container_width=True, key="qm_load"):
                self._load_queue(queue_id)
        with col2:
            if st.button("Clear", use_container_width=True, key="qm_clear"):
                self._clear_queue()

        # Show current queue
        queue_info = self.get_state('queue_info')
        if queue_info:
            st.caption(f"**{queue_info.get('name')}**")
            members = self.get_state('members', [])
            st.caption(f"{len(members)} members")

        # Queue search
        with st.expander("🔍 Search Queues"):
            query = st.text_input("Search", placeholder="Queue name...", key="qm_search", label_visibility="collapsed")
            if query:
                queues = self.api.queues.search(query)
                for q in queues[:8]:
                    if st.button(q.get('name', 'Unknown'), key=f"qm_q_{q.get('id')}", use_container_width=True):
                        self._load_queue(q.get('id'))

        st.markdown("---")

        # Operations
        st.markdown("#### Views")

        queue_loaded = self.get_state('queue_info') is not None

        if st.button("📋 View Members", use_container_width=True, disabled=not queue_loaded, key="qm_nav_view"):
            self.set_state('page', 'view')
            st.rerun()

        if st.button("⚙️ Queue Config", use_container_width=True, disabled=not queue_loaded, key="qm_nav_config"):
            self.set_state('page', 'config')
            st.rerun()

        if st.button("📤 Export", use_container_width=True, disabled=not queue_loaded, key="qm_nav_export"):
            self.set_state('page', 'export')
            st.rerun()

        if st.button("📊 All Queues", use_container_width=True, key="qm_nav_all"):
            self.set_state('page', 'all_queues')
            st.rerun()

    def render_main(self) -> None:
        """Render main content."""
        self.init_state()

        queue_info = self.get_state('queue_info')
        page = self.get_state('page', 'view')

        if page == 'all_queues':
            self._render_all_queues_page()
        elif not queue_info:
            st.markdown("## Queue Manager")
            st.info("Select a queue from the sidebar to begin, or view All Queues.")
        elif page == 'view':
            self._render_view_page()
        elif page == 'config':
            self._render_config_page()
        elif page == 'export':
            self._render_export_page()
        else:
            self._render_view_page()

    def _load_queue(self, queue_id: str) -> None:
        """Load a queue by ID."""
        if not queue_id:
            return

        with st.spinner("Loading queue..."):
            response = self.api.queues.get(queue_id)
            if response.success:
                self.set_state('queue_id', queue_id)
                self.set_state('queue_info', response.data)
                members = self.api.queues.get_members(queue_id)
                self.set_state('members', members)
                st.rerun()
            else:
                self.show_error(f"Failed to load queue: {response.error}")

    def _clear_queue(self) -> None:
        """Clear current queue selection."""
        self.set_state('queue_id', '')
        self.set_state('queue_info', None)
        self.set_state('members', [])
        st.rerun()

    def _refresh_members(self) -> None:
        """Refresh member list."""
        queue_id = self.get_state('queue_id')
        if queue_id:
            members = self.api.queues.get_members(queue_id)
            self.set_state('members', members)

    def _render_view_page(self) -> None:
        """Render view members page."""
        queue_info = self.get_state('queue_info')
        members = self.get_state('members', [])

        st.markdown(f"## {queue_info.get('name')}")
        st.caption(f"{len(members)} members")

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("🔄 Refresh"):
                self._refresh_members()
                st.rerun()

        # Filter
        search = st.text_input("Filter", placeholder="Search by name...")

        # Build dataframe
        df = pd.DataFrame([{
            'Name': m.get('name', 'Unknown'),
            'Email': m.get('email', 'N/A'),
            'Joined': m.get('joined', 'N/A'),
            'ID': m.get('id', '')
        } for m in members])

        if search and not df.empty:
            mask = df['Name'].str.contains(search, case=False, na=False) | \
                   df['Email'].str.contains(search, case=False, na=False)
            df = df[mask]

        st.caption(f"Showing {len(df)} members")
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)

    def _render_config_page(self) -> None:
        """Render queue configuration page."""
        queue_info = self.get_state('queue_info')

        st.markdown(f"## Queue Configuration")
        st.markdown(f"### {queue_info.get('name')}")

        # Display queue details in a clean format
        config_items = [
            ("ID", queue_info.get('id', 'N/A')),
            ("Name", queue_info.get('name', 'N/A')),
            ("Description", queue_info.get('description', 'N/A')),
            ("Media Settings", str(queue_info.get('mediaSettings', {}))),
            ("ACW Settings", str(queue_info.get('acwSettings', {}))),
            ("Skill Evaluation", queue_info.get('skillEvaluationMethod', 'N/A')),
            ("Queue Flow", queue_info.get('queueFlow', {}).get('name', 'N/A') if queue_info.get('queueFlow') else 'N/A'),
            ("Calling Party Name", queue_info.get('callingPartyName', 'N/A')),
            ("Calling Party Number", queue_info.get('callingPartyNumber', 'N/A')),
        ]

        for label, value in config_items:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"**{label}:**")
            with col2:
                st.markdown(str(value) if value else "—")

        # Raw JSON expander
        with st.expander("📄 Raw JSON"):
            st.json(queue_info)

    def _render_export_page(self) -> None:
        """Render export page."""
        queue_info = self.get_state('queue_info')
        members = self.get_state('members', [])

        st.markdown("## Export Queue Data")
        st.caption(f"Queue: **{queue_info.get('name')}** · {len(members)} members")

        df = pd.DataFrame([{
            'Name': m.get('name', 'Unknown'),
            'Email': m.get('email', 'N/A'),
            'ID': m.get('id', '')
        } for m in members])

        st.markdown("### Download Options")

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "📥 Members CSV",
                data=df.to_csv(index=False),
                file_name=f"{queue_info.get('name', 'queue')}_members.csv",
                mime="text/csv",
                use_container_width=True,
                key="qm_export_csv"
            )

        with col2:
            emails = "\n".join(df['Email'].dropna().tolist())
            st.download_button(
                "📥 Emails Only",
                data=emails,
                file_name=f"{queue_info.get('name', 'queue')}_emails.txt",
                mime="text/plain",
                use_container_width=True,
                key="qm_export_emails"
            )

        st.markdown("### Preview")
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)

    def _render_all_queues_page(self) -> None:
        """Render all queues overview page."""
        st.markdown("## All Queues")

        if st.button("🔄 Load All Queues", use_container_width=False):
            with st.spinner("Loading queues..."):
                queues = list(self.api.queues.list(page_size=100, max_pages=5))
                self.set_state('all_queues', queues)
                st.rerun()

        all_queues = self.get_state('all_queues', [])

        if not all_queues:
            st.info("Click 'Load All Queues' to fetch queue data")
            return

        st.caption(f"{len(all_queues)} queues loaded")

        # Filter
        search = st.text_input("Filter queues", placeholder="Search by name...")

        # Build dataframe
        df = pd.DataFrame([{
            'Name': q.get('name', 'Unknown'),
            'Member Count': q.get('memberCount', 0),
            'ID': q.get('id', '')
        } for q in all_queues])

        if search and not df.empty:
            mask = df['Name'].str.contains(search, case=False, na=False)
            df = df[mask]

        st.dataframe(df, use_container_width=True, hide_index=True, height=400)

        # Export option
        st.download_button(
            "📥 Export All Queues (CSV)",
            data=df.to_csv(index=False),
            file_name="all_queues.csv",
            mime="text/csv",
            key="qm_export_all"
        )
