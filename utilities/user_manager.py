"""
User Manager Utility
Search and view user details, groups, skills, and queues.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional

from .base import BaseUtility, UtilityConfig


class UserManagerUtility(BaseUtility):

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="user_manager",
            name="User Manager",
            description="Search users and view details, groups, skills, and queues",
            icon="\U0001F464",
            category="Users & Groups",
            requires_user=True,
            tags=["users", "search", "details", "groups", "skills", "queues"]
        )

    def init_state(self) -> None:
        for key, default in [('page', 'search'), ('user_info', None), ('user_id', '')]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        st.markdown("#### User Manager")

        user_id = st.text_input(
            "User ID", value=self.get_state('user_id', ''),
            placeholder="Paste a User ID", key="um_user_id_input"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Load", use_container_width=True, key="um_load"):
                self._load_user(user_id)
        with col2:
            if st.button("Clear", use_container_width=True, key="um_clear"):
                self._clear_user()

        user_info = self.get_state('user_info')
        if user_info:
            st.caption(f"**{user_info.get('name', '')}**")
            st.caption(user_info.get('email', ''))

        st.markdown("---")
        st.markdown("#### Views")

        loaded = self.get_state('user_info') is not None
        for key, icon, label, page in [
            ("um_nav_search", "\U0001F50D", "Search Users", "search"),
            ("um_nav_detail", "\U0001F4CB", "User Details", "detail"),
            ("um_nav_groups", "\U0001F465", "User Groups", "groups"),
            ("um_nav_skills", "\U0001F3AF", "User Skills", "skills"),
            ("um_nav_queues", "\U0001F4DE", "User Queues", "queues"),
            ("um_nav_all", "\U0001F4CA", "All Users", "all_users"),
        ]:
            disabled = page in ('detail', 'groups', 'skills', 'queues') and not loaded
            if st.button(f"{icon} {label}", use_container_width=True, disabled=disabled, key=key):
                self.set_state('page', page)
                st.rerun()

    def render_main(self) -> None:
        self.init_state()
        page = self.get_state('page', 'search')
        pages = {
            'search': self._page_search, 'detail': self._page_detail,
            'groups': self._page_groups, 'skills': self._page_skills,
            'queues': self._page_queues, 'all_users': self._page_all_users,
        }
        pages.get(page, self._page_search)()

    # -- data helpers --

    def _load_user(self, user_id: str) -> None:
        if not user_id:
            return
        with st.spinner("Loading user..."):
            resp = self.api.users.get(user_id)
            if resp.success:
                self.set_state('user_id', user_id)
                self.set_state('user_info', resp.data)
                self.set_state('page', 'detail')
                st.rerun()
            else:
                st.error(f"User not found: {resp.error}")

    def _load_user_by_email(self, email: str) -> None:
        with st.spinner("Searching..."):
            user = self.api.users.search_by_email(email)
            if user:
                self.set_state('user_id', user['id'])
                self.set_state('user_info', user)
                self.set_state('page', 'detail')
                st.rerun()
            else:
                st.error(f"No user found with email: {email}")

    def _clear_user(self) -> None:
        for key, val in [('user_id', ''), ('user_info', None)]:
            self.set_state(key, val)
        self.set_state('page', 'search')
        st.rerun()

    def _user_header(self) -> None:
        info = self.get_state('user_info')
        if not info:
            return
        st.markdown(f"## {info.get('name', 'User')}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("State", info.get('state', 'N/A'))
        c2.caption(f"**Email:** {info.get('email', '')}")
        c3.caption(f"**Dept:** {info.get('department', 'N/A')}")
        c4.caption(f"**Title:** {info.get('title', 'N/A')}")

    # -- pages --

    def _page_search(self) -> None:
        st.markdown("## Search Users")

        search_query = st.text_input(
            "Search by name or email",
            placeholder="Type a name or email address...",
            key="um_search_input"
        )

        if st.button("Search", type="primary", key="um_search_btn") and search_query:
            with st.spinner("Searching..."):
                if '@' in search_query:
                    user = self.api.users.search_by_email(search_query)
                    results = [user] if user else []
                else:
                    results = self.api.users.search(search_query)

                self.set_state('search_results', results)
                st.rerun()

        results = self.get_state('search_results', [])
        if results:
            st.caption(f"{len(results)} result(s)")

            df = pd.DataFrame([{
                'Name': u.get('name', ''),
                'Email': u.get('email', ''),
                'Department': u.get('department', ''),
                'Title': u.get('title', ''),
                'State': u.get('state', ''),
                'ID': u.get('id', ''),
            } for u in results])

            st.dataframe(df, use_container_width=True, hide_index=True,
                         height=min(400, 35 * len(df) + 38))

            st.markdown("#### Quick Load")
            for u in results[:10]:
                label = f"{u.get('name', '?')} ({u.get('email', '?')})"
                if st.button(label, key=f"um_pick_{u.get('id')}", use_container_width=True):
                    self.set_state('user_id', u['id'])
                    self.set_state('user_info', u)
                    self.set_state('page', 'detail')
                    st.rerun()

    def _page_detail(self) -> None:
        info = self.get_state('user_info')
        if not info:
            st.info("Select a user first.")
            return

        self._user_header()
        st.markdown("---")

        st.markdown("### Profile")
        fields = [
            ("ID", info.get('id')),
            ("Email", info.get('email')),
            ("Name", info.get('name')),
            ("Department", info.get('department')),
            ("Title", info.get('title')),
            ("State", info.get('state')),
            ("Manager", info.get('manager', {}).get('name') if info.get('manager') else None),
            ("Division", info.get('division', {}).get('name') if info.get('division') else None),
        ]

        for label, value in fields:
            c1, c2 = st.columns([1, 3])
            c1.markdown(f"**{label}**")
            c2.markdown(value or "\u2014")

        # Addresses
        addresses = info.get('addresses', [])
        if addresses:
            st.markdown("### Contact")
            for addr in addresses:
                media = addr.get('mediaType', addr.get('type', ''))
                value = addr.get('address', addr.get('display', ''))
                if media or value:
                    c1, c2 = st.columns([1, 3])
                    c1.markdown(f"**{media}**")
                    c2.markdown(value)

        with st.expander("Raw JSON"):
            st.json(info)

    def _page_groups(self) -> None:
        info = self.get_state('user_info')
        if not info:
            st.info("Select a user first.")
            return

        self._user_header()
        st.markdown("### Groups")

        if st.button("Load Groups", key="um_load_groups"):
            with st.spinner("Loading user groups..."):
                resp = self.api.users.get_groups(info['id'])
                if resp.success:
                    data = resp.data
                    groups = data.get('entities', data) if isinstance(data, dict) else data
                    if isinstance(groups, list):
                        self.set_state('user_groups', groups)
                    else:
                        self.set_state('user_groups', [])
                else:
                    st.error(f"Failed: {resp.error}")
                    self.set_state('user_groups', [])
                st.rerun()

        groups = self.get_state('user_groups', [])
        if not groups:
            st.caption("Click 'Load Groups' to see this user's group memberships.")
            return

        st.metric("Groups", len(groups))
        df = pd.DataFrame([{
            'Name': g.get('name', ''),
            'Type': g.get('type', ''),
            'Members': g.get('memberCount', ''),
            'ID': g.get('id', ''),
        } for g in groups])
        st.dataframe(df, use_container_width=True, hide_index=True)

    def _page_skills(self) -> None:
        info = self.get_state('user_info')
        if not info:
            st.info("Select a user first.")
            return

        self._user_header()
        st.markdown("### Skills")

        if st.button("Load Skills", key="um_load_skills"):
            with st.spinner("Loading user skills..."):
                skills = self.api.routing.get_user_skills(info['id'])
                self.set_state('user_skills_list', skills)
                st.rerun()

        skills = self.get_state('user_skills_list', [])
        if not skills:
            st.caption("Click 'Load Skills' to see this user's routing skills.")
            return

        st.metric("Skills", len(skills))
        df = pd.DataFrame([{
            'Skill': s.get('name', ''),
            'Proficiency': s.get('proficiency', 0),
            'State': s.get('state', ''),
            'ID': s.get('id', ''),
        } for s in skills])
        st.dataframe(df, use_container_width=True, hide_index=True)

    def _page_queues(self) -> None:
        info = self.get_state('user_info')
        if not info:
            st.info("Select a user first.")
            return

        self._user_header()
        st.markdown("### Queues")

        if st.button("Load Queues", key="um_load_queues"):
            with st.spinner("Loading user queues..."):
                queues = self.api.users.get_queues(info['id'])
                self.set_state('user_queues_list', queues)
                st.rerun()

        queues = self.get_state('user_queues_list', [])
        if not queues:
            st.caption("Click 'Load Queues' to see this user's queue memberships.")
            return

        st.metric("Queues", len(queues))
        df = pd.DataFrame([{
            'Name': q.get('name', ''),
            'Members': q.get('memberCount', ''),
            'ID': q.get('id', ''),
        } for q in queues])
        st.dataframe(df, use_container_width=True, hide_index=True)

    def _page_all_users(self) -> None:
        st.markdown("## All Users")

        if st.button("Load Users", key="um_load_all"):
            with st.spinner("Loading users (this may take a moment)..."):
                users = list(self.api.users.list(page_size=100, max_pages=5))
                self.set_state('all_users_list', users)
                st.rerun()

        all_users = self.get_state('all_users_list', [])
        if not all_users:
            st.caption("Click 'Load Users' to browse users in your org (up to 500).")
            return

        st.metric("Users Loaded", len(all_users))

        search = st.text_input("Filter", placeholder="Search by name, email, or department...", key="um_all_filter")
        df = pd.DataFrame([{
            'Name': u.get('name', ''),
            'Email': u.get('email', ''),
            'Department': u.get('department', ''),
            'Title': u.get('title', ''),
            'State': u.get('state', ''),
            'ID': u.get('id', ''),
        } for u in all_users])

        if search and not df.empty:
            sl = search.lower()
            mask = (df['Name'].str.lower().str.contains(sl, na=False) |
                    df['Email'].str.lower().str.contains(sl, na=False) |
                    df['Department'].str.lower().str.contains(sl, na=False))
            df = df[mask]

        st.caption(f"Showing {len(df)} users")
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)

        st.download_button("Export CSV", data=df.to_csv(index=False),
                           file_name="users.csv", mime="text/csv", key="um_dl_csv")
