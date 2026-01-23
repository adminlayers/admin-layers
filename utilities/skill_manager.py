"""
Skill Manager Utility
Bulk skill assignment and management for Genesys Cloud users.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional

from .base import BaseUtility, UtilityConfig


class SkillManagerUtility(BaseUtility):
    """
    Utility for managing Genesys Cloud routing skills.

    Features:
    - View all skills in org
    - View user's current skills
    - Bulk assign skills to users
    - Bulk remove skills from users
    - Skill gap analysis
    - Export skill assignments
    """

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="skill_manager",
            name="Skill Manager",
            description="Bulk skill assignment and management",
            icon="🎯",
            category="Routing",
            requires_user=False,
            tags=["skills", "routing", "users", "bulk", "assignment"]
        )

    def init_state(self) -> None:
        """Initialize utility state."""
        if self.get_state('page') is None:
            self.set_state('page', 'skills')
        if self.get_state('skills') is None:
            self.set_state('skills', [])
        if self.get_state('selected_skill') is None:
            self.set_state('selected_skill', None)
        if self.get_state('selected_users') is None:
            self.set_state('selected_users', [])

    def render_sidebar(self) -> None:
        """Render sidebar controls."""
        st.markdown("#### Skill Manager")

        # Load skills button
        if st.button("🔄 Load All Skills", use_container_width=True, key="sm_load_skills"):
            self._load_skills()

        skills = self.get_state('skills', [])
        if skills:
            st.caption(f"{len(skills)} skills loaded")

        st.markdown("---")

        # Navigation
        st.markdown("#### Views")

        if st.button("📋 Skills List", use_container_width=True, key="sm_nav_skills"):
            self.set_state('page', 'skills')
            st.rerun()

        if st.button("👤 User Skills", use_container_width=True, key="sm_nav_user"):
            self.set_state('page', 'user_skills')
            st.rerun()

        if st.button("➕ Bulk Assign", use_container_width=True, key="sm_nav_assign"):
            self.set_state('page', 'assign')
            st.rerun()

        if st.button("➖ Bulk Remove", use_container_width=True, key="sm_nav_remove"):
            self.set_state('page', 'remove')
            st.rerun()

        if st.button("📤 Export", use_container_width=True, key="sm_nav_export"):
            self.set_state('page', 'export')
            st.rerun()

    def render_main(self) -> None:
        """Render main content."""
        self.init_state()

        page = self.get_state('page', 'skills')

        if page == 'skills':
            self._render_skills_page()
        elif page == 'user_skills':
            self._render_user_skills_page()
        elif page == 'assign':
            self._render_assign_page()
        elif page == 'remove':
            self._render_remove_page()
        elif page == 'export':
            self._render_export_page()
        else:
            self._render_skills_page()

    # =========================================================================
    # Page Renderers
    # =========================================================================

    def _render_skills_page(self) -> None:
        """Render skills list page."""
        st.markdown("## Skills List")

        skills = self.get_state('skills', [])

        if not skills:
            st.info("Click 'Load All Skills' in the sidebar to begin.")
            return

        # Filter
        search = st.text_input("Filter skills", placeholder="Search by name...")

        # Build dataframe
        df = pd.DataFrame([{
            'Name': s.get('name', 'Unknown'),
            'State': s.get('state', 'N/A'),
            'ID': s.get('id', '')
        } for s in skills])

        if search and not df.empty:
            mask = df['Name'].str.contains(search, case=False, na=False)
            df = df[mask]

        st.caption(f"Showing {len(df)} skills")
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)

    def _render_user_skills_page(self) -> None:
        """Render user skills lookup page."""
        st.markdown("## User Skills Lookup")

        col1, col2 = st.columns([3, 1])

        with col1:
            user_input = st.text_input(
                "User Email or ID",
                placeholder="user@example.com or user-id",
                key="sm_user_input"
            )

        with col2:
            st.write("")  # Spacer
            st.write("")
            lookup = st.button("Lookup", type="primary", use_container_width=True)

        if lookup and user_input:
            self._lookup_user_skills(user_input)

        # Display results
        user_skills = self.get_state('current_user_skills', [])
        user_info = self.get_state('current_user_info')

        if user_info:
            st.markdown(f"### {user_info.get('name', 'Unknown User')}")
            st.caption(user_info.get('email', ''))

            if user_skills:
                df = pd.DataFrame([{
                    'Skill': s.get('name', 'Unknown'),
                    'Proficiency': s.get('proficiency', 0),
                    'State': s.get('state', 'N/A'),
                    'ID': s.get('id', '')
                } for s in user_skills])

                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning("User has no skills assigned")

    def _render_assign_page(self) -> None:
        """Render bulk skill assignment page."""
        st.markdown("## Bulk Assign Skills")

        skills = self.get_state('skills', [])
        if not skills:
            st.warning("Load skills first from the sidebar")
            return

        # Skill selection
        skill_options = {s.get('name', 'Unknown'): s.get('id') for s in skills}
        selected_skill_name = st.selectbox(
            "Select Skill to Assign",
            options=list(skill_options.keys()),
            key="sm_assign_skill"
        )

        # Proficiency
        proficiency = st.slider(
            "Proficiency Level",
            min_value=0.0,
            max_value=5.0,
            value=3.0,
            step=0.5,
            key="sm_proficiency"
        )

        st.markdown("---")

        # User input
        tab1, tab2 = st.tabs(["Paste Emails", "Upload File"])

        emails_input = ""

        with tab1:
            emails_input = st.text_area(
                "Enter user emails (one per line)",
                height=200,
                placeholder="user1@example.com\nuser2@example.com",
                key="sm_emails_paste"
            )

        with tab2:
            uploaded = st.file_uploader("Upload CSV or TXT", type=['csv', 'txt'], key="sm_upload")
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
            dry_run = st.checkbox("Preview only", value=True, key="sm_dry_run")
        with col2:
            if st.button("Process", type="primary", use_container_width=True, key="sm_process"):
                if emails_input and selected_skill_name:
                    skill_id = skill_options[selected_skill_name]
                    self._process_assign(emails_input, skill_id, selected_skill_name, proficiency, dry_run)

    def _render_remove_page(self) -> None:
        """Render bulk skill removal page."""
        st.markdown("## Bulk Remove Skills")

        skills = self.get_state('skills', [])
        if not skills:
            st.warning("Load skills first from the sidebar")
            return

        # Skill selection
        skill_options = {s.get('name', 'Unknown'): s.get('id') for s in skills}
        selected_skill_name = st.selectbox(
            "Select Skill to Remove",
            options=list(skill_options.keys()),
            key="sm_remove_skill"
        )

        st.markdown("---")

        # User input
        emails_input = st.text_area(
            "Enter user emails (one per line)",
            height=200,
            placeholder="user1@example.com\nuser2@example.com",
            key="sm_remove_emails"
        )

        col1, col2 = st.columns(2)
        with col1:
            dry_run = st.checkbox("Preview only", value=True, key="sm_remove_dry_run")
        with col2:
            confirm = st.checkbox("I confirm removal", key="sm_remove_confirm")

        if st.button("Remove Skills", type="primary", disabled=not confirm and not dry_run, 
                     use_container_width=True, key="sm_remove_btn"):
            if emails_input and selected_skill_name:
                skill_id = skill_options[selected_skill_name]
                self._process_remove(emails_input, skill_id, selected_skill_name, dry_run)

    def _render_export_page(self) -> None:
        """Render export page."""
        st.markdown("## Export Skills")

        skills = self.get_state('skills', [])
        if not skills:
            st.warning("Load skills first from the sidebar")
            return

        df = pd.DataFrame([{
            'Name': s.get('name', 'Unknown'),
            'State': s.get('state', 'N/A'),
            'ID': s.get('id', '')
        } for s in skills])

        st.markdown("### Download Options")

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "📥 CSV (Full)",
                data=df.to_csv(index=False),
                file_name="skills_export.csv",
                mime="text/csv",
                use_container_width=True,
                key="sm_export_csv"
            )

        with col2:
            st.download_button(
                "📥 JSON",
                data=df.to_json(orient='records', indent=2),
                file_name="skills_export.json",
                mime="application/json",
                use_container_width=True,
                key="sm_export_json"
            )

        st.markdown("### Preview")
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)

    # =========================================================================
    # Data Operations
    # =========================================================================

    def _load_skills(self) -> None:
        """Load all skills from org."""
        with st.spinner("Loading skills..."):
            try:
                skills = self.api.routing.get_skills()
                self.set_state('skills', skills)
                self.show_success(f"Loaded {len(skills)} skills")
                st.rerun()
            except Exception as e:
                self.show_error(f"Failed to load skills: {e}")

    def _lookup_user_skills(self, user_input: str) -> None:
        """Look up skills for a user."""
        with st.spinner("Looking up user..."):
            # Try to find user by email first
            user = None
            if '@' in user_input:
                user = self.api.users.search_by_email(user_input)
            else:
                # Assume it's a user ID
                response = self.api.users.get(user_input)
                if response.success:
                    user = response.data

            if not user:
                self.show_error("User not found")
                self.set_state('current_user_info', None)
                self.set_state('current_user_skills', [])
                return

            self.set_state('current_user_info', user)

            # Get user's skills
            user_skills = self.api.routing.get_user_skills(user['id'])
            self.set_state('current_user_skills', user_skills)
            st.rerun()

    def _process_assign(self, emails_input: str, skill_id: str, skill_name: str, 
                        proficiency: float, dry_run: bool) -> None:
        """Process bulk skill assignment."""
        emails = list(dict.fromkeys([
            e.strip() for e in emails_input.split('\n')
            if e.strip() and '@' in e
        ]))

        if not emails:
            self.show_error("No valid emails found")
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
            self.show_success(f"**Found:** {len(found)}")
            for u in found:
                st.caption(f"✓ {u['email']}")

        with col2:
            if not_found:
                self.show_error(f"**Not found:** {len(not_found)}")
                for e in not_found:
                    st.caption(f"✗ {e}")

        if found and not dry_run:
            st.markdown("---")
            st.markdown(f"**Assigning skill:** {skill_name} (proficiency: {proficiency})")

            assign_progress = st.progress(0)
            success_count = 0
            fail_count = 0

            for i, user in enumerate(found):
                assign_progress.progress((i + 1) / len(found))
                response = self.api.routing.add_user_skill(user['id'], skill_id, proficiency)
                if response.success:
                    success_count += 1
                else:
                    fail_count += 1
                    st.caption(f"⚠ Failed for {user['email']}: {response.error}")

            self.show_success(f"Assigned skill to {success_count} users")
            if fail_count:
                self.show_warning(f"{fail_count} assignments failed")

        elif found and dry_run:
            self.show_info(f"Preview complete. Would assign '{skill_name}' to {len(found)} users. Uncheck 'Preview only' to execute.")

    def _process_remove(self, emails_input: str, skill_id: str, skill_name: str, dry_run: bool) -> None:
        """Process bulk skill removal."""
        emails = list(dict.fromkeys([
            e.strip() for e in emails_input.split('\n')
            if e.strip() and '@' in e
        ]))

        if not emails:
            self.show_error("No valid emails found")
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
            self.show_success(f"**Found:** {len(found)}")
            for u in found:
                st.caption(f"✓ {u['email']}")

        with col2:
            if not_found:
                self.show_error(f"**Not found:** {len(not_found)}")
                for e in not_found:
                    st.caption(f"✗ {e}")

        if found and not dry_run:
            st.markdown("---")
            st.markdown(f"**Removing skill:** {skill_name}")

            remove_progress = st.progress(0)
            success_count = 0
            fail_count = 0

            for i, user in enumerate(found):
                remove_progress.progress((i + 1) / len(found))
                response = self.api.routing.remove_user_skill(user['id'], skill_id)
                if response.success:
                    success_count += 1
                else:
                    fail_count += 1
                    st.caption(f"⚠ Failed for {user['email']}: {response.error}")

            self.show_success(f"Removed skill from {success_count} users")
            if fail_count:
                self.show_warning(f"{fail_count} removals failed")

        elif found and dry_run:
            self.show_info(f"Preview complete. Would remove '{skill_name}' from {len(found)} users. Uncheck 'Preview only' to execute.")
