"""
Group Manager Utility
Manage group membership in Genesys Cloud.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional

from .base import BaseUtility, UtilityConfig


class GroupManagerUtility(BaseUtility):

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="group_manager",
            name="Group Manager",
            description="View and manage group membership",
            icon="\U0001F465",
            category="Users & Groups",
            requires_group=True,
            tags=["groups", "users", "membership", "bulk"]
        )

    def init_state(self) -> None:
        for key, default in [('page', 'view'), ('group_id', ''), ('group_info', None), ('members', [])]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        st.markdown("#### Group Selection")

        group_id = st.text_input(
            "Group ID", value=self.get_state('group_id', ''),
            placeholder="Paste a Group ID", key="gm_group_id_input"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Load", use_container_width=True, key="gm_load"):
                self._load_group(group_id)
        with col2:
            if st.button("Clear", use_container_width=True, key="gm_clear"):
                self._clear_group()

        group_info = self.get_state('group_info')
        if group_info:
            st.caption(f"**{group_info.get('name', '')}**")
            st.caption(f"{len(self.get_state('members', []))} members loaded")

        with st.expander("Search Groups"):
            query = st.text_input("Name", placeholder="Type group name...", key="gm_search", label_visibility="collapsed")
            if query:
                results = self.api.groups.search(query)
                if not results:
                    st.caption("No groups found")
                for g in results[:10]:
                    label = f"{g.get('name', '?')} ({g.get('memberCount', '?')} members)"
                    if st.button(label, key=f"gm_g_{g.get('id')}", use_container_width=True):
                        self._load_group(g.get('id'))

        st.markdown("---")
        st.markdown("#### Actions")
        loaded = self.get_state('group_info') is not None
        for key, icon, label, page in [
            ("gm_nav_view", "\U0001F4CB", "View Members", "view"),
            ("gm_nav_add", "\U00002795", "Add Members", "add"),
            ("gm_nav_remove", "\U00002796", "Remove Members", "remove"),
            ("gm_nav_export", "\U0001F4E4", "Export", "export"),
        ]:
            if st.button(f"{icon} {label}", use_container_width=True, disabled=not loaded, key=key):
                self.set_state('page', page)
                st.rerun()

    def render_main(self) -> None:
        self.init_state()
        group_info = self.get_state('group_info')
        if not group_info:
            st.markdown("## Group Manager")
            st.info("Search for a group or paste a Group ID in the sidebar.")
            self._render_all_groups()
            return
        page = self.get_state('page', 'view')
        pages = {'view': self._page_view, 'add': self._page_add,
                 'remove': self._page_remove, 'export': self._page_export}
        pages.get(page, self._page_view)()

    # -- data helpers --

    def _load_group(self, group_id: str) -> None:
        if not group_id:
            return
        with st.spinner("Loading group..."):
            resp = self.api.groups.get(group_id)
            if resp.success:
                self.set_state('group_id', group_id)
                self.set_state('group_info', resp.data)
                self.set_state('members', self.api.groups.get_members(group_id))
                self.set_state('page', 'view')
                st.rerun()
            else:
                st.error(f"Failed to load group: {resp.error}")

    def _clear_group(self) -> None:
        for key, val in [('group_id', ''), ('group_info', None), ('members', [])]:
            self.set_state(key, val)
        st.rerun()

    def _refresh_members(self) -> None:
        gid = self.get_state('group_id')
        if gid:
            self.set_state('members', self.api.groups.get_members(gid))

    def _group_header(self) -> None:
        info = self.get_state('group_info')
        members = self.get_state('members', [])
        st.markdown(f"## {info.get('name', 'Group')}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Members", len(members))
        c2.metric("Type", info.get('type', 'N/A'))
        c3.metric("Visibility", info.get('visibility', 'N/A'))
        if info.get('description'):
            st.caption(info['description'])

    # -- pages --

    def _page_view(self) -> None:
        self._group_header()
        members = self.get_state('members', [])

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Refresh", key="gm_refresh"):
                self._refresh_members()
                st.rerun()

        search = st.text_input("Filter members", placeholder="Name or email...", key="gm_view_filter")

        if not members:
            st.info("This group has no members.")
            return

        df = pd.DataFrame([{
            'Name': m.get('name', ''),
            'Email': m.get('email', ''),
            'Department': m.get('department', ''),
            'ID': m.get('id', ''),
        } for m in members])

        if search and not df.empty:
            mask = (df['Name'].str.contains(search, case=False, na=False) |
                    df['Email'].str.contains(search, case=False, na=False))
            df = df[mask]

        st.caption(f"Showing {len(df)} of {len(members)} members")
        st.dataframe(df, use_container_width=True, hide_index=True, height=min(400, 35 * len(df) + 38))

    def _page_add(self) -> None:
        self._group_header()
        st.markdown("### Add Members")

        tab1, tab2 = st.tabs(["Paste Emails", "Upload File"])
        emails_text = ""
        with tab1:
            emails_text = st.text_area(
                "Emails (one per line)", height=180,
                placeholder="alice@company.com\nbob@company.com", key="gm_paste"
            )
        with tab2:
            uploaded = st.file_uploader("CSV or TXT file", type=['csv', 'txt'], key="gm_upload")
            if uploaded:
                content = uploaded.read().decode('utf-8')
                emails_text = "\n".join(
                    line.split(',')[0].strip().strip('"')
                    for line in content.split('\n') if '@' in line
                )
                st.code(emails_text, language=None)

        c1, c2 = st.columns(2)
        dry_run = c1.checkbox("Preview only (dry run)", value=True, key="gm_dryrun")
        run = c2.button("Process", type="primary", use_container_width=True, key="gm_run_add")

        if run and emails_text:
            self._execute_add(emails_text, dry_run)

    def _execute_add(self, raw: str, dry_run: bool) -> None:
        emails = list(dict.fromkeys(
            e.strip() for e in raw.split('\n') if e.strip() and '@' in e
        ))
        if not emails:
            st.error("No valid email addresses found.")
            return

        st.markdown("---")
        progress = st.progress(0)
        found, missing = [], []
        for i, email in enumerate(emails):
            progress.progress((i + 1) / len(emails))
            user = self.api.users.search_by_email(email)
            if user:
                found.append({'id': user['id'], 'name': user.get('name', ''), 'email': email})
            else:
                missing.append(email)
        progress.empty()

        c1, c2 = st.columns(2)
        with c1:
            st.success(f"**{len(found)}** users found")
            if found:
                st.dataframe(pd.DataFrame(found)[['name', 'email']], hide_index=True, use_container_width=True)
        with c2:
            if missing:
                st.error(f"**{len(missing)}** not found")
                for e in missing:
                    st.caption(f"- {e}")

        if not found:
            return
        if dry_run:
            st.info(f"Dry run complete. {len(found)} users would be added. Uncheck 'Preview only' to execute.")
            return

        resp = self.api.groups.add_members(self.get_state('group_id'), [u['id'] for u in found])
        if resp.success:
            st.success(f"Added {len(found)} members to group.")
            self._refresh_members()
        else:
            st.error(f"Failed: {resp.error}")

    def _page_remove(self) -> None:
        self._group_header()
        st.markdown("### Remove Members")
        members = self.get_state('members', [])
        if not members:
            st.info("No members to remove.")
            return

        search = st.text_input("Filter", placeholder="Search...", key="gm_rm_filter")
        filtered = members
        if search:
            sl = search.lower()
            filtered = [m for m in members
                        if sl in m.get('name', '').lower() or sl in m.get('email', '').lower()]

        options = {f"{m.get('name', '?')} ({m.get('email', '?')})": m.get('id') for m in filtered}
        selected = st.multiselect("Select members to remove", list(options.keys()), key="gm_rm_sel")

        if selected:
            st.warning(f"{len(selected)} member(s) will be removed.")
            confirm = st.checkbox("I confirm this removal", key="gm_rm_confirm")
            if st.button("Remove Selected", type="primary", disabled=not confirm, key="gm_rm_btn"):
                ids = [options[s] for s in selected]
                resp = self.api.groups.remove_members(self.get_state('group_id'), ids)
                if resp.success:
                    st.success(f"Removed {len(selected)} members.")
                    self._refresh_members()
                    st.rerun()
                else:
                    st.error(f"Failed: {resp.error}")

    def _page_export(self) -> None:
        self._group_header()
        st.markdown("### Export")
        members = self.get_state('members', [])
        info = self.get_state('group_info')
        name = info.get('name', 'group')

        df = pd.DataFrame([{
            'Name': m.get('name', ''), 'Email': m.get('email', ''),
            'Department': m.get('department', ''), 'ID': m.get('id', ''),
        } for m in members])

        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Download CSV", data=df.to_csv(index=False),
                               file_name=f"{name}_members.csv", mime="text/csv",
                               use_container_width=True, key="gm_dl_csv")
        with c2:
            emails = "\n".join(df['Email'].dropna().tolist())
            st.download_button("Download Emails", data=emails,
                               file_name=f"{name}_emails.txt", mime="text/plain",
                               use_container_width=True, key="gm_dl_email")

        st.markdown("### Preview")
        st.dataframe(df, use_container_width=True, hide_index=True)

    def _render_all_groups(self) -> None:
        st.markdown("### Browse All Groups")
        if st.button("Load Groups", key="gm_load_all"):
            with st.spinner("Loading..."):
                groups = list(self.api.groups.list(page_size=100))
                self.set_state('all_groups', groups)
                st.rerun()

        all_groups = self.get_state('all_groups', [])
        if not all_groups:
            st.caption("Click 'Load Groups' to browse all groups in your org.")
            return

        search = st.text_input("Filter", placeholder="Search groups...", key="gm_all_filter")
        df = pd.DataFrame([{
            'Name': g.get('name', ''), 'Members': g.get('memberCount', 0),
            'Type': g.get('type', ''), 'Visibility': g.get('visibility', ''),
            'ID': g.get('id', ''),
        } for g in all_groups])

        if search and not df.empty:
            df = df[df['Name'].str.contains(search, case=False, na=False)]

        st.caption(f"{len(df)} groups")
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)
