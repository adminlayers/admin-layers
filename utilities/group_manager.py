"""
Group Manager Utility
Manage group membership in Genesys Cloud.
"""

from typing import Dict, List

import pandas as pd
import streamlit as st

from .base import BaseUtility, UtilityConfig


class GroupManagerUtility(BaseUtility):

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="group_manager",
            name="Group Manager",
            description="View and manage group membership",
            icon="\U0001f465",
            category="Users & Groups",
            requires_group=True,
            tags=["groups", "users", "membership", "bulk"],
        )

    def init_state(self) -> None:
        for key, default in [
            ("page", "list"),
            ("group_id", ""),
            ("group_info", None),
            ("members", []),
            ("all_groups", None),
            ("list_page_size", 25),
            ("list_page_number", 1),
        ]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        st.markdown("#### Group Manager")
        group_info = self.get_state("group_info")
        if group_info:
            st.caption(f"Selected: **{group_info.get('name', '')}**")
        pages = [
            ("gm_nav_list", "\U0001f4cb All Groups", "list"),
            ("gm_nav_create", "\U00002795 Create Group", "create"),
        ]
        if group_info:
            pages += [
                ("gm_nav_detail", "\U0001f465 Members", "detail"),
                ("gm_nav_add", "\U00002795 Add Members", "add"),
                ("gm_nav_remove", "\U00002796 Remove Members", "remove"),
                ("gm_nav_edit", "\U0000270f\ufe0f Edit Group", "edit"),
                ("gm_nav_delete", "\U0001f5d1\ufe0f Delete Group", "delete"),
                ("gm_nav_export", "\U0001f4e5 Export", "export"),
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
            "detail": self._page_detail,
            "add": self._page_add,
            "remove": self._page_remove,
            "export": self._page_export,
            "create": self._page_create,
            "edit": self._page_edit,
            "delete": self._page_delete,
        }.get(page, self._page_list)()

    # -- helpers --

    def _load_group(self, group_id: str) -> None:
        if not group_id:
            return
        resp = self.api.groups.get(group_id)
        if resp.success:
            self.set_state("group_id", group_id)
            self.set_state("group_info", resp.data)
            self.set_state("members", self.api.groups.get_members(group_id))
            self.set_state("page", "detail")
        else:
            st.error(f"Failed to load group: {resp.error}")

    def _refresh_members(self) -> None:
        gid = self.get_state("group_id")
        if gid:
            self.set_state("members", self.api.groups.get_members(gid))

    def _action_bar(self) -> None:
        info = self.get_state("group_info")
        if not info:
            return
        c1, c2, c3, c4, c5 = st.columns(5)
        if c1.button("+ Add", use_container_width=True, key="gm_ab_add"):
            self.set_state("page", "add")
            st.rerun()
        if c2.button("- Remove", use_container_width=True, key="gm_ab_rm"):
            self.set_state("page", "remove")
            st.rerun()
        if c3.button("Export", use_container_width=True, key="gm_ab_exp"):
            self.set_state("page", "export")
            st.rerun()
        if c4.button("Edit", use_container_width=True, key="gm_ab_edit"):
            self.set_state("page", "edit")
            st.rerun()
        if c5.button("Refresh", use_container_width=True, key="gm_ab_ref"):
            self._refresh_members()
            st.rerun()

    def _group_header(self) -> None:
        info = self.get_state("group_info")
        members = self.get_state("members", [])
        if st.button("< Back to Groups", key="gm_back"):
            self.set_state("page", "list")
            st.rerun()
        st.markdown(f"### {info.get('name', 'Group')}")
        desc = info.get("description", "")
        meta = f"**{len(members)}** members · {info.get('type', 'N/A')} · {info.get('visibility', 'N/A')}"
        if desc:
            meta += f" · {desc}"
        st.markdown(meta)
        self._action_bar()
        st.markdown("---")

    # -- pages --

    def _page_list(self) -> None:
        st.markdown("## Groups")
        page_size = self.get_state("list_page_size", 25)
        page_number = self.get_state("list_page_number", 1)

        c1, c2 = st.columns([2, 1])
        with c1:
            page_size = st.selectbox(
                "Rows per page",
                [25, 50, 100],
                index=[25, 50, 100].index(page_size),
                key="gm_page_size",
            )
            self.set_state("list_page_size", page_size)
        with c2:
            page_number = int(
                st.number_input(
                    "Page", min_value=1, value=page_number, step=1, key="gm_page_num"
                )
            )
            self.set_state("list_page_number", page_number)

        with st.spinner("Loading groups..."):
            resp = self.api.groups.list_page(
                page_size=page_size, page_number=page_number
            )
        if not resp.success:
            st.error(f"Failed to load groups: {resp.error}")
            return

        data = resp.data or {}
        all_groups = data.get("entities", [])
        total = data.get("total", len(all_groups))
        page_count = data.get("pageCount", 1)

        if page_number > page_count:
            self.set_state("list_page_number", page_count)
            st.rerun()

        if not all_groups:
            st.info("No groups found in your org.")
            return

        search = st.text_input(
            "Search",
            placeholder="Filter by name...",
            key="gm_list_search",
            label_visibility="collapsed",
        )

        df = pd.DataFrame(
            [
                {
                    "Name": g.get("name", ""),
                    "Members": g.get("memberCount", 0),
                    "Type": g.get("type", ""),
                    "Visibility": g.get("visibility", ""),
                    "ID": g.get("id", ""),
                }
                for g in all_groups
            ]
        )

        if search and not df.empty:
            df = df[df["Name"].str.contains(search, case=False, na=False)]

        st.caption(
            f"Showing {len(df)} of {total} groups (Page {page_number} of {page_count})"
        )
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)

        st.markdown("---")
        st.markdown("##### Open a group")
        filtered = all_groups
        if search:
            sl = search.lower()
            filtered = [g for g in all_groups if sl in g.get("name", "").lower()]
        options = {g.get("name", "?"): g.get("id") for g in filtered}
        if options:
            chosen = st.selectbox(
                "Select group",
                list(options.keys()),
                key="gm_list_pick",
                label_visibility="collapsed",
            )
            if st.button("Open", type="primary", key="gm_list_open"):
                with st.spinner("Loading..."):
                    self._load_group(options[chosen])
                    st.rerun()

    def _page_create(self) -> None:
        st.markdown("## Create Group")
        st.warning(
            "Creating a group affects your org immediately. Confirm before creating."
        )

        with st.form("gm_create_form"):
            name = st.text_input("Name", placeholder="Group name")
            description = st.text_area("Description", placeholder="Group description")
            group_type = st.selectbox("Type", ["official", "custom"], index=0)
            visibility = st.selectbox("Visibility", ["public", "members"], index=0)
            confirm = st.checkbox("I confirm I want to create this group")
            submitted = st.form_submit_button("Create Group", use_container_width=True)

        if submitted:
            if not confirm:
                st.error("Confirmation required before creating a group.")
                return
            if not name:
                st.error("Group name is required.")
                return
            resp = self.api.groups.create(
                name=name,
                description=description,
                group_type=group_type,
                visibility=visibility,
            )
            if resp.success:
                st.success("Group created.")
                self.set_state("group_id", resp.data.get("id"))
                self.set_state("group_info", resp.data)
                self.set_state("page", "detail")
                st.rerun()
            else:
                st.error(f"Failed to create group: {resp.error}")

    def _page_edit(self) -> None:
        info = self.get_state("group_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._group_header()
        st.markdown("### Edit Group")

        with st.form("gm_edit_form"):
            name = st.text_input("Name", value=info.get("name", ""))
            description = st.text_area("Description", value=info.get("description", ""))
            visibility = st.selectbox(
                "Visibility",
                ["public", "members"],
                index=0 if info.get("visibility", "public") == "public" else 1,
            )
            submitted = st.form_submit_button("Save Changes", use_container_width=True)

        if submitted:
            payload = {
                "name": name,
                "description": description,
                "visibility": visibility,
            }
            resp = self.api.groups.update(info.get("id"), payload)
            if resp.success:
                st.success("Group updated.")
                self._load_group(info.get("id"))
                st.rerun()
            else:
                st.error(f"Failed to update group: {resp.error}")

    def _page_delete(self) -> None:
        info = self.get_state("group_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._group_header()
        st.markdown("### Delete Group")
        st.warning("Deleting a group is permanent. This action requires confirmation.")
        confirm = st.checkbox(
            "I understand this will delete the group", key="gm_delete_confirm"
        )
        if st.button(
            "Delete Group", type="primary", disabled=not confirm, key="gm_delete_btn"
        ):
            resp = self.api.groups.delete(info.get("id"))
            if resp.success:
                st.success("Group deleted.")
                self.set_state("group_info", None)
                self.set_state("group_id", "")
                self.set_state("page", "list")
                st.rerun()
            else:
                st.error(f"Failed to delete group: {resp.error}")

    def _page_detail(self) -> None:
        info = self.get_state("group_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._group_header()

        members = self.get_state("members", [])
        search = st.text_input(
            "Filter members", placeholder="Name or email...", key="gm_det_filter"
        )

        if not members:
            st.info("This group has no members.")
            return

        df = pd.DataFrame(
            [
                {
                    "Name": m.get("name", ""),
                    "Email": m.get("email", ""),
                    "Department": m.get("department", ""),
                    "ID": m.get("id", ""),
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
        info = self.get_state("group_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._group_header()
        st.markdown("### Add Members")

        tab1, tab2 = st.tabs(["Paste Emails", "Upload File"])
        emails_text = ""
        with tab1:
            emails_text = st.text_area(
                "Emails (one per line)",
                height=180,
                placeholder="alice@company.com\nbob@company.com",
                key="gm_paste",
            )
        with tab2:
            uploaded = st.file_uploader(
                "CSV or TXT file", type=["csv", "txt"], key="gm_upload"
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
        dry_run = c1.checkbox("Preview only (dry run)", value=True, key="gm_dryrun")
        run = c2.button(
            "Process", type="primary", use_container_width=True, key="gm_run_add"
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
            st.info(f"Dry run complete. {len(found)} users would be added.")
            return

        resp = self.api.groups.add_members(
            self.get_state("group_id"), [u["id"] for u in found]
        )
        if resp.success:
            st.success(f"Added {len(found)} members to group.")
            self._refresh_members()
        else:
            st.error(f"Failed: {resp.error}")

    def _page_remove(self) -> None:
        info = self.get_state("group_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._group_header()
        st.markdown("### Remove Members")

        members = self.get_state("members", [])
        if not members:
            st.info("No members to remove.")
            return

        search = st.text_input("Filter", placeholder="Search...", key="gm_rm_filter")
        filtered = members
        if search:
            sl = search.lower()
            filtered = [
                m
                for m in members
                if sl in m.get("name", "").lower() or sl in m.get("email", "").lower()
            ]

        options = {
            f"{m.get('name', '?')} ({m.get('email', '?')})": m.get("id")
            for m in filtered
        }
        selected = st.multiselect(
            "Select members to remove", list(options.keys()), key="gm_rm_sel"
        )

        if selected:
            st.warning(f"{len(selected)} member(s) will be removed.")
            confirm = st.checkbox("I confirm this removal", key="gm_rm_confirm")
            if st.button(
                "Remove Selected", type="primary", disabled=not confirm, key="gm_rm_btn"
            ):
                ids = [options[s] for s in selected]
                resp = self.api.groups.remove_members(self.get_state("group_id"), ids)
                if resp.success:
                    st.success(f"Removed {len(selected)} members.")
                    self._refresh_members()
                    st.rerun()
                else:
                    st.error(f"Failed: {resp.error}")

    def _page_export(self) -> None:
        info = self.get_state("group_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._group_header()
        st.markdown("### Export")

        members = self.get_state("members", [])
        name = info.get("name", "group")

        df = pd.DataFrame(
            [
                {
                    "Name": m.get("name", ""),
                    "Email": m.get("email", ""),
                    "Department": m.get("department", ""),
                    "ID": m.get("id", ""),
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
                key="gm_dl_csv",
            )
        with c2:
            emails = "\n".join(df["Email"].dropna().tolist())
            st.download_button(
                "Download Emails",
                data=emails,
                file_name=f"{name}_emails.txt",
                mime="text/plain",
                use_container_width=True,
                key="gm_dl_email",
            )

        st.markdown("### Preview")
        st.dataframe(df, use_container_width=True, hide_index=True)
