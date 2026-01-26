"""
Queue Manager Utility
View and manage queue membership in Genesys Cloud.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional

from .base import BaseUtility, UtilityConfig


class QueueManagerUtility(BaseUtility):

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="queue_manager",
            name="Queue Manager",
            description="View and manage queue membership and configuration",
            icon="\U0001F4DE",
            category="Routing",
            requires_queue=True,
            tags=["queues", "routing", "membership", "agents"]
        )

    def init_state(self) -> None:
        for key, default in [('page', 'list'), ('queue_id', ''),
                             ('queue_info', None), ('members', []),
                             ('all_queues', None)]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        st.markdown("#### Queue Manager")
        queue_info = self.get_state('queue_info')
        if queue_info:
            st.caption(f"Selected: **{queue_info.get('name', '')}**")
        pages = [
            ("qm_nav_list", "\U0001F4CB All Queues", "list"),
        ]
        if queue_info:
            pages += [
                ("qm_nav_view", "\U0001F465 Members", "view"),
                ("qm_nav_add", "\U00002795 Add Members", "add"),
                ("qm_nav_remove", "\U00002796 Remove Members", "remove"),
                ("qm_nav_config", "\U00002699\uFE0F Config", "config"),
                ("qm_nav_export", "\U0001F4E5 Export", "export"),
            ]
        for key, label, page in pages:
            if st.button(label, use_container_width=True, key=key):
                self.set_state('page', page)
                st.rerun()

    def render_main(self) -> None:
        self.init_state()
        page = self.get_state('page', 'list')
        {
            'list': self._page_list, 'view': self._page_view,
            'add': self._page_add, 'remove': self._page_remove,
            'config': self._page_config, 'export': self._page_export,
        }.get(page, self._page_list)()

    # -- helpers --

    def _load_queue(self, queue_id: str) -> None:
        if not queue_id:
            return
        resp = self.api.queues.get(queue_id)
        if resp.success:
            self.set_state('queue_id', queue_id)
            self.set_state('queue_info', resp.data)
            self.set_state('members', self.api.queues.get_members(queue_id))
            self.set_state('page', 'view')
        else:
            st.error(f"Failed to load queue: {resp.error}")

    def _refresh_members(self) -> None:
        qid = self.get_state('queue_id')
        if qid:
            self.set_state('members', self.api.queues.get_members(qid))

    def _action_bar(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            return
        c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1, 4])
        if c1.button("\U00002795", help="Add members", key="qm_ab_add"):
            self.set_state('page', 'add')
            st.rerun()
        if c2.button("\U00002796", help="Remove members", key="qm_ab_rm"):
            self.set_state('page', 'remove')
            st.rerun()
        if c3.button("\U00002699\uFE0F", help="Config", key="qm_ab_cfg"):
            self.set_state('page', 'config')
            st.rerun()
        if c4.button("\U0001F4E5", help="Export", key="qm_ab_exp"):
            self.set_state('page', 'export')
            st.rerun()
        if c5.button("\U0001F504", help="Refresh", key="qm_ab_ref"):
            self._refresh_members()
            st.rerun()

    def _queue_header(self) -> None:
        info = self.get_state('queue_info')
        members = self.get_state('members', [])
        c_back, c_title = st.columns([1, 8])
        if c_back.button("\U00002B05", help="Back to list", key="qm_back"):
            self.set_state('page', 'list')
            st.rerun()
        c_title.markdown(f"### {info.get('name', 'Queue')}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Members", len(members))
        c2.metric("Skill Eval", info.get('skillEvaluationMethod', 'N/A'))
        acw = info.get('acwSettings', {})
        acw_timeout = acw.get('timeoutMs')
        c3.metric("ACW", f"{acw_timeout // 1000}s" if acw_timeout else "N/A")
        media = info.get('mediaSettings', {})
        call_settings = media.get('call', {})
        alert = call_settings.get('alertingTimeoutSeconds')
        c4.metric("Alert", f"{alert}s" if alert else "N/A")

        if info.get('description'):
            st.caption(info['description'])
        self._action_bar()
        st.markdown("---")

    # -- pages --

    def _page_list(self) -> None:
        st.markdown("## Queues")
        all_queues = self.get_state('all_queues')

        if all_queues is None:
            with st.spinner("Loading queues..."):
                all_queues = list(self.api.queues.list(page_size=100))
                self.set_state('all_queues', all_queues)

        if not all_queues:
            st.info("No queues found in your org.")
            return

        search = st.text_input("Search", placeholder="Filter by name...",
                               key="qm_list_search", label_visibility="collapsed")

        df = pd.DataFrame([{
            'Name': q.get('name', ''),
            'Members': q.get('memberCount', 0),
            'Skill Eval': q.get('skillEvaluationMethod', ''),
            'ID': q.get('id', ''),
        } for q in all_queues])

        if search and not df.empty:
            df = df[df['Name'].str.contains(search, case=False, na=False)]

        st.caption(f"{len(df)} queues")
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)

        st.markdown("---")
        st.markdown("##### Open a queue")
        filtered = all_queues
        if search:
            sl = search.lower()
            filtered = [q for q in all_queues if sl in q.get('name', '').lower()]
        options = {f"{q.get('name', '?')} ({q.get('memberCount', '?')} members)": q.get('id') for q in filtered}
        if options:
            chosen = st.selectbox("Select queue", list(options.keys()), key="qm_list_pick",
                                  label_visibility="collapsed")
            if st.button("Open", type="primary", key="qm_list_open"):
                with st.spinner("Loading..."):
                    self._load_queue(options[chosen])
                    st.rerun()

    def _page_view(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            self.set_state('page', 'list')
            st.rerun()
            return
        self._queue_header()

        members = self.get_state('members', [])
        search = st.text_input("Filter members", placeholder="Name or email...", key="qm_view_filter")

        if not members:
            st.info("This queue has no members.")
            return

        df = pd.DataFrame([{
            'Name': m.get('name', m.get('user', {}).get('name', '')),
            'Email': m.get('email', m.get('user', {}).get('email', '')),
            'Joined': str(m.get('joined', '')),
            'ID': m.get('id', m.get('user', {}).get('id', '')),
        } for m in members])

        if search and not df.empty:
            mask = (df['Name'].str.contains(search, case=False, na=False) |
                    df['Email'].str.contains(search, case=False, na=False))
            df = df[mask]

        st.caption(f"Showing {len(df)} of {len(members)}")
        st.dataframe(df, use_container_width=True, hide_index=True, height=min(500, 35 * len(df) + 38))

    def _page_add(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            self.set_state('page', 'list')
            st.rerun()
            return
        self._queue_header()
        st.markdown("### Add Members")

        tab1, tab2 = st.tabs(["Paste Emails", "Upload File"])
        emails_text = ""
        with tab1:
            emails_text = st.text_area(
                "Emails (one per line)", height=180,
                placeholder="agent1@company.com\nagent2@company.com", key="qm_paste"
            )
        with tab2:
            uploaded = st.file_uploader("CSV or TXT file", type=['csv', 'txt'], key="qm_upload")
            if uploaded:
                content = uploaded.read().decode('utf-8')
                emails_text = "\n".join(
                    line.split(',')[0].strip().strip('"')
                    for line in content.split('\n') if '@' in line
                )
                st.code(emails_text, language=None)

        c1, c2 = st.columns(2)
        dry_run = c1.checkbox("Preview only (dry run)", value=True, key="qm_dryrun")
        run = c2.button("Process", type="primary", use_container_width=True, key="qm_run_add")

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
            st.info(f"Dry run complete. {len(found)} users would be added. Uncheck 'Preview only' to execute.")
            return

        resp = self.api.queues.add_members(self.get_state('queue_id'), [u['id'] for u in found])
        if resp.success:
            st.success(f"Added {len(found)} members to queue.")
            self._refresh_members()
        else:
            st.error(f"Failed: {resp.error}")

    def _page_remove(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            self.set_state('page', 'list')
            st.rerun()
            return
        self._queue_header()
        st.markdown("### Remove Members")

        members = self.get_state('members', [])
        if not members:
            st.info("No members to remove.")
            return

        search = st.text_input("Filter", placeholder="Search...", key="qm_rm_filter")
        filtered = members
        if search:
            sl = search.lower()
            filtered = [m for m in members if
                        sl in m.get('name', m.get('user', {}).get('name', '')).lower() or
                        sl in m.get('email', m.get('user', {}).get('email', '')).lower()]

        def _label(m):
            name = m.get('name', m.get('user', {}).get('name', '?'))
            email = m.get('email', m.get('user', {}).get('email', '?'))
            return f"{name} ({email})"

        def _id(m):
            return m.get('id', m.get('user', {}).get('id', ''))

        options = {_label(m): _id(m) for m in filtered}
        selected = st.multiselect("Select members to remove", list(options.keys()), key="qm_rm_sel")

        if selected:
            st.warning(f"{len(selected)} agent(s) will be removed from queue.")
            confirm = st.checkbox("I confirm this removal", key="qm_rm_confirm")
            if st.button("Remove Selected", type="primary", disabled=not confirm, key="qm_rm_btn"):
                ids = [options[s] for s in selected]
                resp = self.api.queues.remove_members(self.get_state('queue_id'), ids)
                if resp.success:
                    st.success(f"Removed {len(selected)} members from queue.")
                    self._refresh_members()
                    st.rerun()
                else:
                    st.error(f"Failed: {resp.error}")

    def _page_config(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            self.set_state('page', 'list')
            st.rerun()
            return
        self._queue_header()
        st.markdown("### Configuration")

        # General
        st.markdown("#### General")
        rows = [
            ("ID", info.get('id', '')),
            ("Name", info.get('name', '')),
            ("Description", info.get('description', '')),
            ("Skill Evaluation", info.get('skillEvaluationMethod', '')),
            ("Calling Party Name", info.get('callingPartyName', '')),
            ("Calling Party Number", info.get('callingPartyNumber', '')),
        ]
        for label, value in rows:
            c1, c2 = st.columns([1, 3])
            c1.markdown(f"**{label}**")
            c2.markdown(value or "\u2014")

        # ACW Settings
        acw = info.get('acwSettings', {})
        if acw:
            st.markdown("#### After Call Work")
            c1, c2 = st.columns([1, 3])
            c1.markdown("**Wrapup Prompt**")
            c2.markdown(acw.get('wrapupPrompt', '\u2014'))
            c1, c2 = st.columns([1, 3])
            c1.markdown("**Timeout**")
            timeout = acw.get('timeoutMs')
            c2.markdown(f"{timeout // 1000} seconds" if timeout else "\u2014")

        # Media Settings
        media = info.get('mediaSettings', {})
        if media:
            st.markdown("#### Media Settings")
            for media_type, settings in media.items():
                if isinstance(settings, dict):
                    alert = settings.get('alertingTimeoutSeconds')
                    if alert:
                        c1, c2 = st.columns([1, 3])
                        c1.markdown(f"**{media_type.title()} Alert**")
                        c2.markdown(f"{alert} seconds")

        # Queue Flow
        qf = info.get('queueFlow')
        if qf:
            st.markdown("#### Queue Flow")
            c1, c2 = st.columns([1, 3])
            c1.markdown("**Flow**")
            c2.markdown(qf.get('name', qf.get('id', '\u2014')))

        with st.expander("Raw JSON"):
            st.json(info)

    def _page_export(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            self.set_state('page', 'list')
            st.rerun()
            return
        self._queue_header()
        st.markdown("### Export")

        members = self.get_state('members', [])
        name = info.get('name', 'queue')

        df = pd.DataFrame([{
            'Name': m.get('name', m.get('user', {}).get('name', '')),
            'Email': m.get('email', m.get('user', {}).get('email', '')),
            'ID': m.get('id', m.get('user', {}).get('id', '')),
        } for m in members])

        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Download CSV", data=df.to_csv(index=False),
                               file_name=f"{name}_members.csv", mime="text/csv",
                               use_container_width=True, key="qm_dl_csv")
        with c2:
            emails = "\n".join(df['Email'].dropna().tolist())
            st.download_button("Download Emails", data=emails,
                               file_name=f"{name}_emails.txt", mime="text/plain",
                               use_container_width=True, key="qm_dl_email")

        st.markdown("### Preview")
        st.dataframe(df, use_container_width=True, hide_index=True)
