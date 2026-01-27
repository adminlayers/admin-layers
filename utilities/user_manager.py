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
        for key, default in [('page', 'list'), ('user_info', None),
                             ('user_id', ''), ('all_users', None),
                             ('list_page_size', 25), ('list_page_number', 1)]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        st.markdown("#### User Manager")
        user_info = self.get_state('user_info')
        if user_info:
            st.caption(f"Selected: **{user_info.get('name', '')}**")

        pages = [
            ("um_nav_list", "\U0001F4CB All Users", "list"),
            ("um_nav_search", "\U0001F50D Search", "search"),
        ]
        if user_info:
            pages += [
                ("um_nav_detail", "\U0001F4C4 Details", "detail"),
                ("um_nav_edit", "\U0000270F\ufe0f Edit Details", "edit"),
                ("um_nav_groups", "\U0001F465 Groups", "groups"),
                ("um_nav_skills", "\U0001F3AF Skills", "skills"),
                ("um_nav_queues", "\U0001F4DE Queues", "queues"),
            ]
        for key, label, page in pages:
            if st.button(label, use_container_width=True, key=key):
                self.set_state('page', page)
                st.rerun()

    def render_main(self) -> None:
        self.init_state()
        page = self.get_state('page', 'list')
        pages = {
            'list': self._page_list, 'search': self._page_search,
            'detail': self._page_detail, 'groups': self._page_groups,
            'skills': self._page_skills, 'queues': self._page_queues,
            'edit': self._page_edit,
        }
        pages.get(page, self._page_list)()

    # -- data helpers --

    def _load_user(self, user_id: str) -> None:
        if not user_id:
            return
        resp = self.api.users.get(user_id)
        if resp.success:
            self.set_state('user_id', user_id)
            self.set_state('user_info', resp.data)
            self.set_state('page', 'detail')
        else:
            st.error(f"User not found: {resp.error}")

    def _load_user_by_email(self, email: str) -> None:
        user = self.api.users.search_by_email(email)
        if user:
            self.set_state('user_id', user['id'])
            self.set_state('user_info', user)
            self.set_state('page', 'detail')
        else:
            st.error(f"No user found with email: {email}")

    def _clear_user(self) -> None:
        for key, val in [('user_id', ''), ('user_info', None)]:
            self.set_state(key, val)
        self.set_state('page', 'list')
        st.rerun()

    def _action_bar(self) -> None:
        info = self.get_state('user_info')
        if not info:
            return
        c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1, 4])
        if c1.button("\U0001F465", help="Groups", key="um_ab_groups"):
            self.set_state('page', 'groups')
            st.rerun()
        if c2.button("\U0001F3AF", help="Skills", key="um_ab_skills"):
            self.set_state('page', 'skills')
            st.rerun()
        if c3.button("\U0001F4DE", help="Queues", key="um_ab_queues"):
            self.set_state('page', 'queues')
            st.rerun()
        if c4.button("\U0000270F\ufe0f", help="Edit", key="um_ab_edit"):
            self.set_state('page', 'edit')
            st.rerun()
        if c5.button("\U0001F504", help="Refresh", key="um_ab_ref"):
            self._load_user(self.get_state('user_id'))
            st.rerun()

    def _user_header(self) -> None:
        info = self.get_state('user_info')
        if not info:
            return
        c_back, c_title = st.columns([1, 8])
        if c_back.button("\U00002B05", help="Back to list", key="um_back"):
            self._clear_user()
            return
        c_title.markdown(f"### {info.get('name', 'User')}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("State", info.get('state', 'N/A'))
        c2.caption(f"**Email:** {info.get('email', '')}")
        c3.caption(f"**Dept:** {info.get('department', 'N/A')}")
        c4.caption(f"**Title:** {info.get('title', 'N/A')}")
        self._action_bar()
        st.markdown("---")

    # -- pages --

    def _page_list(self) -> None:
        st.markdown("## Users")
        page_size = self.get_state('list_page_size', 25)
        page_number = self.get_state('list_page_number', 1)

        c1, c2 = st.columns([2, 1])
        with c1:
            page_size = st.selectbox(
                "Rows per page",
                [25, 50, 100],
                index=[25, 50, 100].index(page_size),
                key="um_page_size",
            )
            self.set_state('list_page_size', page_size)
        with c2:
            page_number = int(st.number_input("Page", min_value=1, value=page_number, step=1, key="um_page_num"))
            self.set_state('list_page_number', page_number)

        with st.spinner("Loading users (this may take a moment)..."):
            resp = self.api.users.list_page(page_size=page_size, page_number=page_number)
        if not resp.success:
            st.error(f"Failed to load users: {resp.error}")
            return

        data = resp.data or {}
        all_users = data.get('entities', [])
        total = data.get('total', len(all_users))
        page_count = data.get('pageCount', 1)

        if page_number > page_count:
            self.set_state('list_page_number', page_count)
            st.rerun()

        if not all_users:
            st.info("No users found in your org.")
            return

        st.metric("Users Loaded", total)

        search = st.text_input("Search", placeholder="Filter by name, email, or department...",
                               key="um_list_search", label_visibility="collapsed")

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

        st.caption(f"Showing {len(df)} of {total} users (Page {page_number} of {page_count})")
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)

        st.markdown("---")
        st.markdown("##### Open a user")
        filtered = all_users
        if search:
            sl = search.lower()
            filtered = [u for u in all_users
                        if sl in u.get('name', '').lower()
                        or sl in u.get('email', '').lower()
                        or sl in u.get('department', '').lower()]
        options = {f"{u.get('name', '?')} ({u.get('email', '?')})": u.get('id') for u in filtered}
        if options:
            chosen = st.selectbox("Select user", list(options.keys()), key="um_list_pick",
                                  label_visibility="collapsed")
            if st.button("Open", type="primary", key="um_list_open"):
                with st.spinner("Loading..."):
                    self._load_user(options[chosen])
                    st.rerun()

        st.markdown("---")
        st.download_button("Export CSV", data=df.to_csv(index=False),
                           file_name="users.csv", mime="text/csv", key="um_dl_csv")

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
            self.set_state('page', 'list')
            st.rerun()
            return

        self._user_header()

        st.markdown("## User Profile")
        st.caption("Expanded profile view with quick actions to manage group, skill, and queue access.")

        stats = st.columns(4)
        stats[0].metric("State", info.get('state', 'N/A'))
        stats[1].metric("Department", info.get('department', 'N/A'))
        stats[2].metric("Title", info.get('title', 'N/A'))
        stats[3].metric("ID", info.get('id', ''))

        st.markdown("---")
        st.markdown("### Profile Details")
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

        st.markdown("---")
        st.markdown("## Quick Actions")
        tab_group, tab_skill, tab_queue = st.tabs(["Add to Group", "Assign Skill", "Add to Queue"])

        with tab_group:
            group_query = st.text_input("Search groups", placeholder="Start typing a group name...", key="um_quick_group")
            group_options = []
            if group_query:
                group_options = self.api.groups.search(group_query)
            if group_options:
                group_map = {g.get('name', '?'): g.get('id') for g in group_options}
                selected_group = st.selectbox("Select group", list(group_map.keys()), key="um_quick_group_pick")
                confirm = st.checkbox("I confirm adding this user to the group", key="um_quick_group_confirm")
                if st.button("Add to Group", type="primary", disabled=not confirm, key="um_quick_group_btn"):
                    resp = self.api.groups.add_members(group_map[selected_group], [info['id']])
                    if resp.success:
                        st.success("User added to group.")
                        self.set_state('user_groups', None)
                    else:
                        st.error(f"Failed to add to group: {resp.error}")
            else:
                st.caption("Enter a group search term to load matches.")

        with tab_skill:
            skills = self.api.routing.get_skills()
            if skills:
                skill_map = {s.get('name', ''): s.get('id') for s in skills}
                selected_skill = st.selectbox("Select skill", list(skill_map.keys()), key="um_quick_skill_pick")
                proficiency = st.slider("Proficiency", 0.0, 5.0, 3.0, 0.5, key="um_quick_prof")
                confirm = st.checkbox("I confirm assigning this skill", key="um_quick_skill_confirm")
                if st.button("Assign Skill", type="primary", disabled=not confirm, key="um_quick_skill_btn"):
                    resp = self.api.routing.add_user_skill(info['id'], skill_map[selected_skill], proficiency)
                    if resp.success:
                        st.success("Skill assigned.")
                        self.set_state('user_skills_list', None)
                    else:
                        st.error(f"Failed to assign skill: {resp.error}")
            else:
                st.info("No skills available.")

        with tab_queue:
            queue_query = st.text_input("Search queues", placeholder="Start typing a queue name...", key="um_quick_queue")
            queue_options = []
            if queue_query:
                queue_options = self.api.queues.search(queue_query)
            if queue_options:
                queue_map = {q.get('name', '?'): q.get('id') for q in queue_options}
                selected_queue = st.selectbox("Select queue", list(queue_map.keys()), key="um_quick_queue_pick")
                confirm = st.checkbox("I confirm adding this user to the queue", key="um_quick_queue_confirm")
                if st.button("Add to Queue", type="primary", disabled=not confirm, key="um_quick_queue_btn"):
                    resp = self.api.queues.add_members(queue_map[selected_queue], [info['id']])
                    if resp.success:
                        st.success("User added to queue.")
                        self.set_state('user_queues_list', None)
                    else:
                        st.error(f"Failed to add to queue: {resp.error}")
            else:
                st.caption("Enter a queue search term to load matches.")

    def _page_edit(self) -> None:
        info = self.get_state('user_info')
        if not info:
            self.set_state('page', 'list')
            st.rerun()
            return

        self._user_header()
        st.markdown("### Edit User Details")

        with st.form("um_edit_form"):
            name = st.text_input("Name", value=info.get('name', ''))
            department = st.text_input("Department", value=info.get('department', ''))
            title = st.text_input("Title", value=info.get('title', ''))
            state = st.selectbox(
                "State",
                ["active", "inactive"],
                index=0 if info.get("state", "active") == "active" else 1,
            )
            confirm = st.checkbox("I confirm updating this user", key="um_edit_confirm")
            submitted = st.form_submit_button("Save Changes", use_container_width=True)

        if submitted:
            if not confirm:
                st.error("Confirmation required before updating the user.")
                return
            payload = {
                "name": name,
                "department": department,
                "title": title,
                "state": state,
            }
            resp = self.api.users.update(info['id'], payload)
            if resp.success:
                st.success("User updated.")
                self._load_user(info['id'])
                st.rerun()
            else:
                st.error(f"Failed to update user: {resp.error}")

    def _page_groups(self) -> None:
        info = self.get_state('user_info')
        if not info:
            self.set_state('page', 'list')
            st.rerun()
            return

        self._user_header()
        st.markdown("### Groups")

        groups = self.get_state('user_groups')

        if groups is None:
            with st.spinner("Loading user groups..."):
                resp = self.api.users.get_groups(info['id'])
                if resp.success:
                    data = resp.data
                    groups = data.get('entities', data) if isinstance(data, dict) else data
                    if not isinstance(groups, list):
                        groups = []
                else:
                    st.error(f"Failed: {resp.error}")
                    groups = []
                self.set_state('user_groups', groups)

        if st.button("Refresh", key="um_grp_refresh"):
            self.set_state('user_groups', None)
            st.rerun()

        if not groups:
            st.info("No groups found for this user.")
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
            self.set_state('page', 'list')
            st.rerun()
            return

        self._user_header()
        st.markdown("### Skills")

        skills = self.get_state('user_skills_list')

        if skills is None:
            with st.spinner("Loading user skills..."):
                skills = self.api.routing.get_user_skills(info['id'])
                self.set_state('user_skills_list', skills)

        if st.button("Refresh", key="um_skills_refresh"):
            self.set_state('user_skills_list', None)
            st.rerun()

        if not skills:
            st.info("No skills assigned to this user.")
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
            self.set_state('page', 'list')
            st.rerun()
            return

        self._user_header()
        st.markdown("### Queues")

        queues = self.get_state('user_queues_list')

        if queues is None:
            with st.spinner("Loading user queues..."):
                queues = self.api.users.get_queues(info['id'])
                self.set_state('user_queues_list', queues)

        if st.button("Refresh", key="um_queues_refresh"):
            self.set_state('user_queues_list', None)
            st.rerun()

        if not queues:
            st.info("No queues found for this user.")
            return

        st.metric("Queues", len(queues))
        df = pd.DataFrame([{
            'Name': q.get('name', ''),
            'Members': q.get('memberCount', ''),
            'ID': q.get('id', ''),
        } for q in queues])
        st.dataframe(df, use_container_width=True, hide_index=True)
