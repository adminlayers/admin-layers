"""
Queue Manager Utility
View and manage queue membership in Genesys Cloud.
"""

from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from .base import BaseUtility, UtilityConfig


class QueueManagerUtility(BaseUtility):

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="queue_manager",
            name="Queue Manager",
            description="View and manage queue membership and configuration",
            icon="\U0001f4de",
            category="Routing",
            requires_queue=True,
            tags=["queues", "routing", "membership", "agents"],
        )

    def init_state(self) -> None:
        for key, default in [
            ("page", "list"),
            ("queue_id", ""),
            ("queue_info", None),
            ("members", []),
            ("all_queues", None),
            ("list_page_size", 25),
            ("list_page_number", 1),
        ]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        st.markdown("#### Queue Manager")
        queue_info = self.get_state("queue_info")
        if queue_info:
            st.caption(f"Selected: **{queue_info.get('name', '')}**")
        pages = [
            ("qm_nav_list", "\U0001f4cb All Queues", "list"),
            ("qm_nav_create", "\U00002795 Create Queue", "create"),
        ]
        if queue_info:
            pages += [
                ("qm_nav_view", "\U0001f465 Members", "view"),
                ("qm_nav_add", "\U00002795 Add Members", "add"),
                ("qm_nav_remove", "\U00002796 Remove Members", "remove"),
                ("qm_nav_config", "\U00002699\ufe0f Config", "config"),
                ("qm_nav_edit", "\U0000270f\ufe0f Edit Queue", "edit"),
                ("qm_nav_delete", "\U0001f5d1\ufe0f Delete Queue", "delete"),
                ("qm_nav_export", "\U0001f4e5 Export", "export"),
            ]
        for key, label, page in pages:
            if st.button(label, use_container_width=True, key=key):
                self.set_state("page", page)
                st.rerun()

    def render_main(self) -> None:
        self.init_state()
        page = self.get_state("page", "list")
        {
            "list": self._page_list,
            "view": self._page_view,
            "add": self._page_add,
            "remove": self._page_remove,
            "config": self._page_config,
            "export": self._page_export,
            "create": self._page_create,
            "edit": self._page_edit,
            "delete": self._page_delete,
        }.get(page, self._page_list)()

    # -- helpers --

    def _load_queue(self, queue_id: str) -> None:
        if not queue_id:
            return
        resp = self.api.queues.get(queue_id)
        if resp.success:
            self.set_state("queue_id", queue_id)
            self.set_state("queue_info", resp.data)
            self.set_state("members", self.api.queues.get_members(queue_id))
            self.set_state("page", "view")
        else:
            st.error(f"Failed to load queue: {resp.error}")

    def _refresh_members(self) -> None:
        qid = self.get_state("queue_id")
        if qid:
            self.set_state("members", self.api.queues.get_members(qid))

    def _action_bar(self) -> None:
        info = self.get_state("queue_info")
        if not info:
            return
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        if c1.button("+ Add", use_container_width=True, key="qm_ab_add"):
            self.set_state("page", "add")
            st.rerun()
        if c2.button("- Remove", use_container_width=True, key="qm_ab_rm"):
            self.set_state("page", "remove")
            st.rerun()
        if c3.button("Config", use_container_width=True, key="qm_ab_cfg"):
            self.set_state("page", "config")
            st.rerun()
        if c4.button("Export", use_container_width=True, key="qm_ab_exp"):
            self.set_state("page", "export")
            st.rerun()
        if c5.button("Edit", use_container_width=True, key="qm_ab_edit"):
            self.set_state("page", "edit")
            st.rerun()
        if c6.button("Refresh", use_container_width=True, key="qm_ab_ref"):
            self._refresh_members()
            st.rerun()

    def _queue_header(self) -> None:
        info = self.get_state("queue_info")
        members = self.get_state("members", [])
        if st.button("< Back to Queues", key="qm_back"):
            self.set_state("page", "list")
            st.rerun()
        st.markdown(f"### {info.get('name', 'Queue')}")

        acw = info.get("acwSettings", {})
        acw_timeout = acw.get("timeoutMs")
        acw_str = f"{acw_timeout // 1000}s" if acw_timeout else "N/A"
        media = info.get("mediaSettings", {})
        call_settings = media.get("call", {})
        alert = call_settings.get("alertingTimeoutSeconds")
        alert_str = f"{alert}s" if alert else "N/A"

        meta = (
            f"**{len(members)}** members · "
            f"Skill eval: {info.get('skillEvaluationMethod', 'N/A')} · "
            f"ACW: {acw_str} · Alert: {alert_str}"
        )
        st.markdown(meta)

        if info.get("description"):
            st.caption(info["description"])
        self._action_bar()
        st.markdown("---")

    # -- pages --

    def _page_list(self) -> None:
        st.markdown("## Queues")
        page_size = self.get_state("list_page_size", 25)
        page_number = self.get_state("list_page_number", 1)

        c1, c2 = st.columns([2, 1])
        with c1:
            page_size = st.selectbox(
                "Rows per page",
                [25, 50, 100],
                index=[25, 50, 100].index(page_size),
                key="qm_page_size",
            )
            self.set_state("list_page_size", page_size)
        with c2:
            page_number = int(
                st.number_input(
                    "Page", min_value=1, value=page_number, step=1, key="qm_page_num"
                )
            )
            self.set_state("list_page_number", page_number)

        with st.spinner("Loading queues..."):
            resp = self.api.queues.list_page(
                page_size=page_size, page_number=page_number
            )
        if not resp.success:
            st.error(f"Failed to load queues: {resp.error}")
            return

        data = resp.data or {}
        all_queues = data.get("entities", [])
        total = data.get("total", len(all_queues))
        page_count = data.get("pageCount", 1)

        if page_number > page_count:
            self.set_state("list_page_number", page_count)
            st.rerun()

        if not all_queues:
            st.info("No queues found in your org.")
            return

        search = st.text_input(
            "Search",
            placeholder="Filter by name...",
            key="qm_list_search",
            label_visibility="collapsed",
        )

        df = pd.DataFrame(
            [
                {
                    "Name": q.get("name", ""),
                    "Members": q.get("memberCount", 0),
                    "Skill Eval": q.get("skillEvaluationMethod", ""),
                    "ID": q.get("id", ""),
                }
                for q in all_queues
            ]
        )

        if search and not df.empty:
            df = df[df["Name"].str.contains(search, case=False, na=False)]

        st.caption(
            f"Showing {len(df)} of {total} queues (Page {page_number} of {page_count})"
        )
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)

        st.markdown("---")
        st.markdown("##### Open a queue")
        filtered = all_queues
        if search:
            sl = search.lower()
            filtered = [q for q in all_queues if sl in q.get("name", "").lower()]
        options = {
            f"{q.get('name', '?')} ({q.get('memberCount', '?')} members)": q.get("id")
            for q in filtered
        }
        if options:
            chosen = st.selectbox(
                "Select queue",
                list(options.keys()),
                key="qm_list_pick",
                label_visibility="collapsed",
            )
            if st.button("Open", type="primary", key="qm_list_open"):
                with st.spinner("Loading..."):
                    self._load_queue(options[chosen])
                    st.rerun()

    def _page_create(self) -> None:
        st.markdown("## Create Queue")
        st.warning("Creating a queue affects routing. Confirm before creating.")

        with st.form("qm_create_form"):
            name = st.text_input("Name", placeholder="Queue name")
            description = st.text_area("Description", placeholder="Queue description")
            skill_eval = st.selectbox("Skill Evaluation", ["BEST", "ALL"], index=0)
            calling_party_name = st.text_input(
                "Calling Party Name", placeholder="Outbound display name"
            )
            calling_party_number = st.text_input(
                "Calling Party Number", placeholder="+18005551234"
            )
            acw_timeout = st.number_input(
                "ACW Timeout (seconds)", min_value=0, value=60, step=5
            )
            alert_timeout = st.number_input(
                "Alert Timeout (seconds)", min_value=0, value=30, step=5
            )
            confirm = st.checkbox("I confirm I want to create this queue")
            submitted = st.form_submit_button("Create Queue", use_container_width=True)

        if submitted:
            if not confirm:
                st.error("Confirmation required before creating a queue.")
                return
            if not name:
                st.error("Queue name is required.")
                return
            payload = {
                "name": name,
                "description": description,
                "skillEvaluationMethod": skill_eval,
                "callingPartyName": calling_party_name,
                "callingPartyNumber": calling_party_number,
                "acwSettings": {
                    "wrapupPrompt": "MANDATORY",
                    "timeoutMs": int(acw_timeout * 1000),
                },
                "mediaSettings": {
                    "call": {"alertingTimeoutSeconds": int(alert_timeout)}
                },
            }
            resp = self.api.queues.create(payload)
            if resp.success:
                st.success("Queue created.")
                self.set_state("queue_id", resp.data.get("id"))
                self.set_state("queue_info", resp.data)
                self.set_state("page", "view")
                st.rerun()
            else:
                st.error(f"Failed to create queue: {resp.error}")

    def _page_edit(self) -> None:
        info = self.get_state("queue_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._queue_header()
        st.markdown("### Edit Queue")

        acw = info.get("acwSettings", {}) or {}
        media = info.get("mediaSettings", {}) or {}
        call_settings = media.get("call", {}) if isinstance(media, dict) else {}

        with st.form("qm_edit_form"):
            name = st.text_input("Name", value=info.get("name", ""))
            description = st.text_area("Description", value=info.get("description", ""))
            skill_eval = st.selectbox(
                "Skill Evaluation",
                ["BEST", "ALL"],
                index=0 if info.get("skillEvaluationMethod", "BEST") == "BEST" else 1,
            )
            calling_party_name = st.text_input(
                "Calling Party Name", value=info.get("callingPartyName", "")
            )
            calling_party_number = st.text_input(
                "Calling Party Number", value=info.get("callingPartyNumber", "")
            )
            acw_timeout = st.number_input(
                "ACW Timeout (seconds)",
                min_value=0,
                value=int((acw.get("timeoutMs") or 60000) / 1000),
                step=5,
            )
            alert_timeout = st.number_input(
                "Alert Timeout (seconds)",
                min_value=0,
                value=int(call_settings.get("alertingTimeoutSeconds") or 30),
                step=5,
            )
            submitted = st.form_submit_button("Save Changes", use_container_width=True)

        if submitted:
            payload = {
                "name": name,
                "description": description,
                "skillEvaluationMethod": skill_eval,
                "callingPartyName": calling_party_name,
                "callingPartyNumber": calling_party_number,
                "acwSettings": {
                    "wrapupPrompt": acw.get("wrapupPrompt", "MANDATORY"),
                    "timeoutMs": int(acw_timeout * 1000),
                },
                "mediaSettings": {
                    "call": {"alertingTimeoutSeconds": int(alert_timeout)}
                },
            }
            resp = self.api.queues.update(info.get("id"), payload)
            if resp.success:
                st.success("Queue updated.")
                self._load_queue(info.get("id"))
                st.rerun()
            else:
                st.error(f"Failed to update queue: {resp.error}")

    def _page_delete(self) -> None:
        info = self.get_state("queue_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._queue_header()
        st.markdown("### Delete Queue")
        st.warning("Deleting a queue is permanent. This action requires confirmation.")
        confirm = st.checkbox(
            "I understand this will delete the queue", key="qm_delete_confirm"
        )
        if st.button(
            "Delete Queue", type="primary", disabled=not confirm, key="qm_delete_btn"
        ):
            resp = self.api.queues.delete(info.get("id"))
            if resp.success:
                st.success("Queue deleted.")
                self.set_state("queue_info", None)
                self.set_state("queue_id", "")
                self.set_state("page", "list")
                st.rerun()
            else:
                st.error(f"Failed to delete queue: {resp.error}")

    def _page_view(self) -> None:
        info = self.get_state("queue_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._queue_header()

        members = self.get_state("members", [])
        search = st.text_input(
            "Filter members", placeholder="Name or email...", key="qm_view_filter"
        )

        if not members:
            st.info("This queue has no members.")
            return

        df = pd.DataFrame(
            [
                {
                    "Name": m.get("name", m.get("user", {}).get("name", "")),
                    "Email": m.get("email", m.get("user", {}).get("email", "")),
                    "Joined": str(m.get("joined", "")),
                    "ID": m.get("id", m.get("user", {}).get("id", "")),
                }
                for m in members
            ]
        )

        if search and not df.empty:
            mask = df["Name"].str.contains(search, case=False, na=False) | df[
                "Email"
            ].str.contains(search, case=False, na=False)
            df = df[mask]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=min(500, 35 * len(df) + 38),
        )

    def _page_add(self) -> None:
        info = self.get_state("queue_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._queue_header()
        st.markdown("### Add Members")

        tab1, tab2 = st.tabs(["Paste Emails", "Upload File"])
        emails_text = ""
        with tab1:
            emails_text = st.text_area(
                "Emails (one per line)",
                height=180,
                placeholder="agent1@company.com\nagent2@company.com",
                key="qm_paste",
            )
        with tab2:
            uploaded = st.file_uploader(
                "CSV or TXT file", type=["csv", "txt"], key="qm_upload"
            )
            if uploaded:
                content = uploaded.read().decode("utf-8")
                emails_text = "\n".join(
                    line.split(",")[0].strip().strip('"')
                    for line in content.split("\n")
                    if "@" in line
                )
                st.code(emails_text, language=None)

        c1, c2 = st.columns(2)
        dry_run = c1.checkbox("Preview only (dry run)", value=True, key="qm_dryrun")
        run = c2.button(
            "Process", type="primary", use_container_width=True, key="qm_run_add"
        )

        if run and emails_text:
            self._execute_add(emails_text, dry_run)

    def _execute_add(self, raw: str, dry_run: bool) -> None:
        emails = list(
            dict.fromkeys(e.strip() for e in raw.split("\n") if e.strip() and "@" in e)
        )
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
                found.append(
                    {"id": user["id"], "name": user.get("name", ""), "email": email}
                )
            else:
                missing.append(email)
        progress.empty()

        c1, c2 = st.columns(2)
        with c1:
            st.success(f"**{len(found)}** users found")
            if found:
                st.dataframe(
                    pd.DataFrame(found)[["name", "email"]],
                    hide_index=True,
                    use_container_width=True,
                )
        with c2:
            if missing:
                st.error(f"**{len(missing)}** not found")
                for e in missing:
                    st.caption(f"- {e}")

        if not found:
            return
        if dry_run:
            st.info(
                f"Dry run complete. {len(found)} users would be added. Uncheck 'Preview only' to execute."
            )
            return

        resp = self.api.queues.add_members(
            self.get_state("queue_id"), [u["id"] for u in found]
        )
        if resp.success:
            st.success(f"Added {len(found)} members to queue.")
            self._refresh_members()
        else:
            st.error(f"Failed: {resp.error}")

    def _page_remove(self) -> None:
        info = self.get_state("queue_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._queue_header()
        st.markdown("### Remove Members")

        members = self.get_state("members", [])
        if not members:
            st.info("No members to remove.")
            return

        search = st.text_input("Filter", placeholder="Search...", key="qm_rm_filter")
        filtered = members
        if search:
            sl = search.lower()
            filtered = [
                m
                for m in members
                if sl in m.get("name", m.get("user", {}).get("name", "")).lower()
                or sl in m.get("email", m.get("user", {}).get("email", "")).lower()
            ]

        def _label(m):
            name = m.get("name", m.get("user", {}).get("name", "?"))
            email = m.get("email", m.get("user", {}).get("email", "?"))
            return f"{name} ({email})"

        def _id(m):
            return m.get("id", m.get("user", {}).get("id", ""))

        options = {_label(m): _id(m) for m in filtered}
        selected = st.multiselect(
            "Select members to remove", list(options.keys()), key="qm_rm_sel"
        )

        if selected:
            st.warning(f"{len(selected)} agent(s) will be removed from queue.")
            confirm = st.checkbox("I confirm this removal", key="qm_rm_confirm")
            if st.button(
                "Remove Selected", type="primary", disabled=not confirm, key="qm_rm_btn"
            ):
                ids = [options[s] for s in selected]
                resp = self.api.queues.remove_members(self.get_state("queue_id"), ids)
                if resp.success:
                    st.success(f"Removed {len(selected)} members from queue.")
                    self._refresh_members()
                    st.rerun()
                else:
                    st.error(f"Failed: {resp.error}")

    def _page_config(self) -> None:
        info = self.get_state("queue_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._queue_header()
        st.markdown("### Configuration")

        # General
        st.markdown("#### General")
        rows = [
            ("ID", info.get("id", "")),
            ("Name", info.get("name", "")),
            ("Description", info.get("description", "")),
            ("Skill Evaluation", info.get("skillEvaluationMethod", "")),
            ("Calling Party Name", info.get("callingPartyName", "")),
            ("Calling Party Number", info.get("callingPartyNumber", "")),
        ]
        for label, value in rows:
            c1, c2 = st.columns([1, 3])
            c1.markdown(f"**{label}**")
            c2.markdown(value or "\u2014")

        # ACW Settings
        acw = info.get("acwSettings", {})
        if acw:
            st.markdown("#### After Call Work")
            c1, c2 = st.columns([1, 3])
            c1.markdown("**Wrapup Prompt**")
            c2.markdown(acw.get("wrapupPrompt", "\u2014"))
            c1, c2 = st.columns([1, 3])
            c1.markdown("**Timeout**")
            timeout = acw.get("timeoutMs")
            c2.markdown(f"{timeout // 1000} seconds" if timeout else "\u2014")

        # Media Settings
        media = info.get("mediaSettings", {})
        if media:
            st.markdown("#### Media Settings")
            for media_type, settings in media.items():
                if isinstance(settings, dict):
                    alert = settings.get("alertingTimeoutSeconds")
                    if alert:
                        c1, c2 = st.columns([1, 3])
                        c1.markdown(f"**{media_type.title()} Alert**")
                        c2.markdown(f"{alert} seconds")

        # Queue Flow
        qf = info.get("queueFlow")
        if qf:
            st.markdown("#### Queue Flow")
            c1, c2 = st.columns([1, 3])
            c1.markdown("**Flow**")
            c2.markdown(qf.get("name", qf.get("id", "\u2014")))

        with st.expander("Raw JSON"):
            st.json(info)

    def _page_export(self) -> None:
        info = self.get_state("queue_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._queue_header()
        st.markdown("### Export")

        members = self.get_state("members", [])
        name = info.get("name", "queue")

        df = pd.DataFrame(
            [
                {
                    "Name": m.get("name", m.get("user", {}).get("name", "")),
                    "Email": m.get("email", m.get("user", {}).get("email", "")),
                    "ID": m.get("id", m.get("user", {}).get("id", "")),
                }
                for m in members
            ]
        )

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "Download CSV",
                data=df.to_csv(index=False),
                file_name=f"{name}_members.csv",
                mime="text/csv",
                use_container_width=True,
                key="qm_dl_csv",
            )
        with c2:
            emails = "\n".join(df["Email"].dropna().tolist())
            st.download_button(
                "Download Emails",
                data=emails,
                file_name=f"{name}_emails.txt",
                mime="text/plain",
                use_container_width=True,
                key="qm_dl_email",
            )

        st.markdown("### Preview")
        st.dataframe(df, use_container_width=True, hide_index=True)
