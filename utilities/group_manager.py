"""
Group Manager Utility
Manage group membership in Genesys Cloud.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict

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
        for key, default in [('page', 'list'), ('group_id', ''),
                             ('group_info', None), ('members', []),
                             ('all_groups', None)]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        st.markdown("#### Group Manager")
        group_info = self.get_state('group_info')
        if group_info:
            st.caption(f"Selected: **{group_info.get('name', '')}**")
        pages = [
            ("gm_nav_list", "\U0001F4CB All Groups", "list"),
        ]
        if group_info:
            pages += [
                ("gm_nav_detail", "\U0001F465 Members", "detail"),
                ("gm_nav_add", "\U00002795 Add Members", "add"),
                ("gm_nav_remove", "\U00002796 Remove Members", "remove"),
                ("gm_nav_export", "\U0001F4E5 Export", "export"),
            ]
        for key, label, page in pages:
            if st.button(label, use_container_width=True, key=key):
                self.set_state('page', page)
                st.rerun()

    def render_main(self) -> None:
        self.init_state()
        page = self.get_state('page', 'list')
        {'list': self._page_list, 'detail': self._page_detail,
         'add': self._page_add, 'remove': self._page_remove,
         'export': self._page_export}.get(page, self._page_list)()

    # -- helpers --

    def _load_group(self, group_id: str) -> None:
        if not group_id:
            return
        resp = self.api.groups.get(group_id)
        if resp.success:
            self.set_state('group_id', group_id)
            self.set_state('group_info', resp.data)
            self.set_state('members', self.api.groups.get_members(group_id))
            self.set_state('page', 'detail')
        else:
            st.error(f"Failed to load group: {resp.error}")

    def _refresh_members(self) -> None:
        gid = self.get_state('group_id')
        if gid:
            self.set_state('members', self.api.groups.get_members(gid))

    def _action_bar(self) -> None:
        info = self.get_state('group_info')
        if not info:
            return
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 5])
        if c1.button("\U00002795", help="Add members", key="gm_ab_add"):
            self.set_state('page', 'add')
            st.rerun()
        if c2.button("\U00002796", help="Remove members", key="gm_ab_rm"):
            self.set_state('page', 'remove')
            st.rerun()
        if c3.button("\U0001F4E5", help="Export", key="gm_ab_exp"):
            self.set_state('page', 'export')
            st.rerun()
        if c4.button("\U0001F504", help="Refresh", key="gm_ab_ref"):
            self._refresh_members()
            st.rerun()

    def _group_header(self) -> None:
        info = self.get_state('group_info')
        members = self.get_state('members', [])
        c_back, c_title = st.columns([1, 8])
        if c_back.button("\U00002B05", help="Back to list", key="gm_back"):
            self.set_state('page', 'list')
            st.rerun()
        c_title.markdown(f"### {info.get('name', 'Group')}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Members", len(members))
        c2.metric("Type", info.get('type', 'N/A'))
        c3.metric("Visibility", info.get('visibility', 'N/A'))
        if info.get('description'):
            st.caption(info['description'])
        self._action_bar()
        st.markdown("---")

    # -- pages --

    def _page_list(self) -> None:
        st.markdown("## Groups")
        all_groups = self.get_state('all_groups')

        if all_groups is None:
            with st.spinner("Loading groups..."):
                all_groups = list(self.api.groups.list(page_size=100))
                self.set_state('all_groups', all_groups)

        if not all_groups:
            st.info("No groups found in your org.")
            return

        search = st.text_input("Search", placeholder="Filter by name...",
                               key="gm_list_search", label_visibility="collapsed")

        df = pd.DataFrame([{
            'Name': g.get('name', ''),
            'Members': g.get('memberCount', 0),
            'Type': g.get('type', ''),
            'Visibility': g.get('visibility', ''),
            'ID': g.get('id', ''),
        } for g in all_groups])

        if search and not df.empty:
            df = df[df['Name'].str.contains(search, case=False, na=False)]

        st.caption(f"{len(df)} groups")
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)

        st.markdown("---")
        st.markdown("##### Open a group")
        filtered = all_groups
        if search:
            sl = search.lower()
            filtered = [g for g in all_groups if sl in g.get('name', '').lower()]
        options = {g.get('name', '?'): g.get('id') for g in filtered}
        if options:
            chosen = st.selectbox("Select group", list(options.keys()), key="gm_list_pick",
                                  label_visibility="collapsed")
            if st.button("Open", type="primary", key="gm_list_open"):
                with st.spinner("Loading..."):
                    self._load_group(options[chosen])
                    st.rerun()

    def _page_detail(self) -> None:
        info = self.get_state('group_info')
        if not info:
            self.set_state('page', 'list')
            st.rerun()
            return
        self._group_header()

        members = self.get_state('members', [])
        search = st.text_input("Filter members", placeholder="Name or email...", key="gm_det_filter")

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

        st.caption(f"Showing {len(df)} of {len(members)}")
        st.dataframe(df, use_container_width=True, hide_index=True, height=min(500, 35 * len(df) + 38))

    def _page_add(self) -> None:
        info = self.get_state('group_info')
        if not info:
            self.set_state('page', 'list')
            st.rerun()
            return
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
                st.dataframe(pd.DataFrame(found)[['name', 'email']],
                             hide_index=True, use_container_width=True)
        with c2:
            if missing:
                st.error(f"**{len(missing)}** not found")
                for e in missing:
                    st.caption(f"- {e}")

        if not found:
            return
        if dry_run:
            st.info(f"Dry run complete. {len(found)} users would be added.")
            return

        resp = self.api.groups.add_members(self.get_state('group_id'), [u['id'] for u in found])
        if resp.success:
            st.success(f"Added {len(found)} members to group.")
            self._refresh_members()
        else:
            st.error(f"Failed: {resp.error}")

    def _page_remove(self) -> None:
        info = self.get_state('group_info')
        if not info:
            self.set_state('page', 'list')
            st.rerun()
            return
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
        info = self.get_state('group_info')
        if not info:
            self.set_state('page', 'list')
            st.rerun()
            return
        self._group_header()
        st.markdown("### Export")

        members = self.get_state('members', [])
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
