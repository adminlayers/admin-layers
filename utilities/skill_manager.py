"""
Skill Manager Utility
Bulk skill assignment and management for Genesys Cloud.
"""

from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from .base import BaseUtility, UtilityConfig


class SkillManagerUtility(BaseUtility):

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="skill_manager",
            name="Skill Manager",
            description="Bulk skill assignment and user skill lookup",
            icon="\U0001f3af",
            category="Routing",
            requires_user=False,
            tags=["skills", "routing", "users", "bulk", "assignment"],
        )

    def init_state(self) -> None:
        for key, default in [
            ("page", "list"),
            ("skills", []),
            ("selected_skill", None),
            ("selected_users", []),
            ("skill_id", ""),
            ("skill_info", None),
            ("list_page_size", 25),
            ("list_page_number", 1),
        ]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        st.markdown("#### Skill Manager")

        skills = self.get_state("skills", [])
        if skills:
            st.caption(f"{len(skills)} skills loaded")

        pages = [
            ("sm_nav_list", "\U0001f4cb All Skills", "list"),
            ("sm_nav_create", "\U00002795 Create Skill", "create"),
            ("sm_nav_user", "\U0001f464 User Skills", "user_skills"),
            ("sm_nav_assign", "\U00002795 Bulk Assign", "assign"),
            ("sm_nav_remove", "\U00002796 Bulk Remove", "remove"),
            ("sm_nav_export", "\U0001f4e4 Export", "export"),
        ]
        skill_info = self.get_state("skill_info")
        if skill_info:
            pages += [
                ("sm_nav_detail", "\U0001f4c4 Skill Details", "detail"),
                ("sm_nav_edit", "\U0000270f\ufe0f Edit Skill", "edit"),
                ("sm_nav_delete", "\U0001f5d1\ufe0f Delete Skill", "delete"),
            ]
        for key, label, page in pages:
            if st.button(label, use_container_width=True, key=key):
                self.set_state("page", page)
                st.rerun()

    def render_main(self) -> None:
        self.init_state()
        page = self.get_state("page", "list")
        pages = {
            "list": self._page_list,
            "user_skills": self._page_user_skills,
            "assign": self._page_assign,
            "remove": self._page_remove,
            "export": self._page_export,
            "create": self._page_create,
            "detail": self._page_detail,
            "edit": self._page_edit,
            "delete": self._page_delete,
        }
        pages.get(page, self._page_list)()

    def _load_skill(self, skill_id: str) -> None:
        resp = self.api.routing.get_skill(skill_id)
        if resp.success:
            self.set_state("skill_id", skill_id)
            self.set_state("skill_info", resp.data)
            self.set_state("page", "detail")
        else:
            st.error(f"Failed to load skill: {resp.error}")

    def _skill_action_bar(self) -> None:
        info = self.get_state("skill_info")
        if not info:
            return
        c1, c2, c3 = st.columns([1, 1, 6])
        if c1.button("\U0000270f\ufe0f", help="Edit", key="sm_ab_edit"):
            self.set_state("page", "edit")
            st.rerun()
        if c2.button("\U0001f504", help="Refresh", key="sm_ab_refresh"):
            self._load_skill(info.get("id"))
            st.rerun()

    def _skill_header(self) -> None:
        info = self.get_state("skill_info")
        if not info:
            return
        c_back, c_title = st.columns([1, 8])
        if c_back.button("\U00002b05", help="Back to list", key="sm_back"):
            self.set_state("page", "list")
            st.rerun()
        c_title.markdown(f"### {info.get('name', 'Skill')}")
        c1, c2 = st.columns(2)
        c1.metric("State", info.get("state", "N/A"))
        c2.caption(f"**ID:** {info.get('id', '')}")
        if info.get("description"):
            st.caption(info["description"])
        self._skill_action_bar()
        st.markdown("---")

    # -- data helpers --

    def _load_skills(self) -> List[Dict]:
        with st.spinner("Loading skills..."):
            try:
                skills = self.api.routing.get_skills()
                self.set_state("skills", skills)
                return skills
            except Exception as e:
                st.error(f"Failed to load skills: {e}")
                return []

    def _ensure_skills(self) -> List[Dict]:
        skills = self.get_state("skills", [])
        if not skills:
            skills = self._load_skills()
        return skills

    # -- pages --

    def _page_list(self) -> None:
        st.markdown("## Skills")
        page_size = self.get_state("list_page_size", 25)
        page_number = self.get_state("list_page_number", 1)

        c1, c2 = st.columns([2, 1])
        with c1:
            page_size = st.selectbox(
                "Rows per page",
                [25, 50, 100],
                index=[25, 50, 100].index(page_size),
                key="sm_page_size",
            )
            self.set_state("list_page_size", page_size)
        with c2:
            page_number = int(
                st.number_input(
                    "Page", min_value=1, value=page_number, step=1, key="sm_page_num"
                )
            )
            self.set_state("list_page_number", page_number)

        with st.spinner("Loading skills..."):
            resp = self.api.routing.list_skills_page(
                page_size=page_size, page_number=page_number
            )
        if not resp.success:
            st.error(f"Failed to load skills: {resp.error}")
            return

        data = resp.data or {}
        skills = data.get("entities", [])
        total = data.get("total", len(skills))
        page_count = data.get("pageCount", 1)

        if page_number > page_count:
            self.set_state("list_page_number", page_count)
            st.rerun()

        if not skills:
            st.info("No skills found in your org.")
            return

        active = sum(1 for s in skills if s.get("state") == "active")
        st.caption(f"{len(skills)} skills ({active} active)")

        search = st.text_input(
            "Search",
            placeholder="Filter skills...",
            key="sm_list_search",
            label_visibility="collapsed",
        )

        df = pd.DataFrame(
            [
                {
                    "Name": s.get("name", ""),
                    "State": s.get("state", ""),
                    "ID": s.get("id", ""),
                }
                for s in skills
            ]
        )

        if search and not df.empty:
            df = df[df["Name"].str.contains(search, case=False, na=False)]

        st.caption(
            f"Showing {len(df)} of {total} skills (Page {page_number} of {page_count})"
        )
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=min(500, 35 * len(df) + 38),
        )

        st.markdown("---")
        st.markdown("##### Open a skill")
        filtered = skills
        if search:
            sl = search.lower()
            filtered = [s for s in skills if sl in s.get("name", "").lower()]
        options = {s.get("name", "?"): s.get("id") for s in filtered}
        if options:
            chosen = st.selectbox(
                "Select skill",
                list(options.keys()),
                key="sm_list_pick",
                label_visibility="collapsed",
            )
            if st.button("Open", type="primary", key="sm_list_open"):
                with st.spinner("Loading..."):
                    self._load_skill(options[chosen])
                    st.rerun()

    def _page_detail(self) -> None:
        info = self.get_state("skill_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._skill_header()

        st.markdown("### Details")
        fields = [
            ("ID", info.get("id")),
            ("Name", info.get("name")),
            ("State", info.get("state")),
            ("Description", info.get("description")),
        ]
        for label, value in fields:
            c1, c2 = st.columns([1, 3])
            c1.markdown(f"**{label}**")
            c2.markdown(value or "\u2014")

        with st.expander("Raw JSON"):
            st.json(info)

    def _page_create(self) -> None:
        st.markdown("## Create Skill")
        st.warning("Creating a skill affects routing. Confirm before creating.")

        with st.form("sm_create_form"):
            name = st.text_input("Name", placeholder="Skill name")
            description = st.text_area("Description", placeholder="Skill description")
            state = st.selectbox("State", ["active", "inactive"], index=0)
            confirm = st.checkbox("I confirm I want to create this skill")
            submitted = st.form_submit_button("Create Skill", use_container_width=True)

        if submitted:
            if not confirm:
                st.error("Confirmation required before creating a skill.")
                return
            if not name:
                st.error("Skill name is required.")
                return
            resp = self.api.routing.create_skill(
                name=name, description=description, state=state
            )
            if resp.success:
                st.success("Skill created.")
                self.set_state("skills", [])
                self.set_state("skill_id", resp.data.get("id"))
                self.set_state("skill_info", resp.data)
                self.set_state("page", "detail")
                st.rerun()
            else:
                st.error(f"Failed to create skill: {resp.error}")

    def _page_edit(self) -> None:
        info = self.get_state("skill_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._skill_header()
        st.markdown("### Edit Skill")

        with st.form("sm_edit_form"):
            name = st.text_input("Name", value=info.get("name", ""))
            description = st.text_area("Description", value=info.get("description", ""))
            state = st.selectbox(
                "State",
                ["active", "inactive"],
                index=0 if info.get("state", "active") == "active" else 1,
            )
            submitted = st.form_submit_button("Save Changes", use_container_width=True)

        if submitted:
            payload = {"name": name, "description": description, "state": state}
            resp = self.api.routing.update_skill(info.get("id"), payload)
            if resp.success:
                st.success("Skill updated.")
                self.set_state("skills", [])
                self._load_skill(info.get("id"))
                st.rerun()
            else:
                st.error(f"Failed to update skill: {resp.error}")

    def _page_delete(self) -> None:
        info = self.get_state("skill_info")
        if not info:
            self.set_state("page", "list")
            st.rerun()
            return
        self._skill_header()
        st.markdown("### Delete Skill")
        st.warning("Deleting a skill is permanent. This action requires confirmation.")
        confirm = st.checkbox(
            "I understand this will delete the skill", key="sm_delete_confirm"
        )
        if st.button(
            "Delete Skill", type="primary", disabled=not confirm, key="sm_delete_btn"
        ):
            resp = self.api.routing.delete_skill(info.get("id"))
            if resp.success:
                st.success("Skill deleted.")
                self.set_state("skills", [])
                self.set_state("skill_info", None)
                self.set_state("skill_id", "")
                self.set_state("page", "list")
                st.rerun()
            else:
                st.error(f"Failed to delete skill: {resp.error}")

    def _page_user_skills(self) -> None:
        st.markdown("## User Skills Lookup")

        c1, c2 = st.columns([4, 1])
        with c1:
            user_input = st.text_input(
                "User email or ID", placeholder="user@example.com", key="sm_user_input"
            )
        with c2:
            st.markdown("")
            st.markdown("")
            lookup = st.button(
                "Lookup", type="primary", use_container_width=True, key="sm_lookup_btn"
            )

        if lookup and user_input:
            self._lookup_user_skills(user_input)

        user_info = self.get_state("current_user_info")
        user_skills = self.get_state("current_user_skills", [])

        if user_info:
            st.markdown("---")
            st.markdown(f"### {user_info.get('name', 'Unknown')}")
            st.markdown(
                f"{len(user_skills)} skill(s) · "
                f"{user_info.get('email', '')} · "
                f"ID: {user_info.get('id', '')}"
            )

            if user_skills:
                df = pd.DataFrame(
                    [
                        {
                            "Skill": s.get("name", ""),
                            "Proficiency": s.get("proficiency", 0),
                            "State": s.get("state", ""),
                            "ID": s.get("id", ""),
                        }
                        for s in user_skills
                    ]
                )
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No skills assigned to this user.")

    def _lookup_user_skills(self, user_input: str) -> None:
        with st.spinner("Looking up user..."):
            user = None
            if "@" in user_input:
                user = self.api.users.search_by_email(user_input)
            else:
                resp = self.api.users.get(user_input)
                if resp.success:
                    user = resp.data

            if not user:
                st.error("User not found.")
                self.set_state("current_user_info", None)
                self.set_state("current_user_skills", [])
                return

            self.set_state("current_user_info", user)
            user_skills = self.api.routing.get_user_skills(user["id"])
            self.set_state("current_user_skills", user_skills)
            st.rerun()

    def _page_assign(self) -> None:
        st.markdown("## Bulk Assign Skill")
        skills = self._ensure_skills()
        if not skills:
            return

        skill_map = {s.get("name", ""): s.get("id") for s in skills}
        selected_name = st.selectbox(
            "Skill to assign", list(skill_map.keys()), key="sm_assign_skill"
        )

        proficiency = st.slider("Proficiency", 0.0, 5.0, 3.0, 0.5, key="sm_prof")

        st.markdown("---")

        tab1, tab2 = st.tabs(["Paste Emails", "Upload File"])
        emails_text = ""
        with tab1:
            emails_text = st.text_area(
                "Emails (one per line)",
                height=180,
                placeholder="user1@company.com\nuser2@company.com",
                key="sm_paste",
            )
        with tab2:
            uploaded = st.file_uploader(
                "CSV or TXT", type=["csv", "txt"], key="sm_upload"
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
        dry_run = c1.checkbox("Preview only (dry run)", value=True, key="sm_dryrun")
        run = c2.button(
            "Process", type="primary", use_container_width=True, key="sm_run_assign"
        )

        if run and emails_text and selected_name:
            skill_id = skill_map[selected_name]
            self._execute_assign(
                emails_text, skill_id, selected_name, proficiency, dry_run
            )

    def _execute_assign(
        self,
        raw: str,
        skill_id: str,
        skill_name: str,
        proficiency: float,
        dry_run: bool,
    ) -> None:
        emails = list(
            dict.fromkeys(e.strip() for e in raw.split("\n") if e.strip() and "@" in e)
        )
        if not emails:
            st.error("No valid emails found.")
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
                f"Dry run: would assign '{skill_name}' (proficiency {proficiency}) to {len(found)} users."
            )
            return

        st.markdown("---")
        st.markdown(f"**Assigning:** {skill_name} (proficiency {proficiency})")
        prog = st.progress(0)
        ok, fail = 0, 0
        for i, u in enumerate(found):
            prog.progress((i + 1) / len(found))
            resp = self.api.routing.add_user_skill(u["id"], skill_id, proficiency)
            if resp.success:
                ok += 1
            else:
                fail += 1
                st.caption(f"Failed for {u['email']}: {resp.error}")
        prog.empty()

        st.success(f"Assigned to {ok} users.")
        if fail:
            st.warning(f"{fail} failed.")

    def _page_remove(self) -> None:
        st.markdown("## Bulk Remove Skill")
        skills = self._ensure_skills()
        if not skills:
            return

        skill_map = {s.get("name", ""): s.get("id") for s in skills}
        selected_name = st.selectbox(
            "Skill to remove", list(skill_map.keys()), key="sm_rm_skill"
        )

        st.markdown("---")

        emails_text = st.text_area(
            "User emails (one per line)",
            height=180,
            placeholder="user1@company.com\nuser2@company.com",
            key="sm_rm_emails",
        )

        c1, c2 = st.columns(2)
        dry_run = c1.checkbox("Preview only (dry run)", value=True, key="sm_rm_dryrun")
        confirm = c2.checkbox("I confirm removal", key="sm_rm_confirm")

        if st.button(
            "Remove Skill",
            type="primary",
            disabled=not confirm and not dry_run,
            use_container_width=True,
            key="sm_rm_btn",
        ):
            if emails_text and selected_name:
                skill_id = skill_map[selected_name]
                self._execute_remove(emails_text, skill_id, selected_name, dry_run)

    def _execute_remove(
        self, raw: str, skill_id: str, skill_name: str, dry_run: bool
    ) -> None:
        emails = list(
            dict.fromkeys(e.strip() for e in raw.split("\n") if e.strip() and "@" in e)
        )
        if not emails:
            st.error("No valid emails found.")
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
        with c2:
            if missing:
                st.error(f"**{len(missing)}** not found")

        if not found:
            return
        if dry_run:
            st.info(f"Dry run: would remove '{skill_name}' from {len(found)} users.")
            return

        st.markdown("---")
        st.markdown(f"**Removing:** {skill_name}")
        prog = st.progress(0)
        ok, fail = 0, 0
        for i, u in enumerate(found):
            prog.progress((i + 1) / len(found))
            resp = self.api.routing.remove_user_skill(u["id"], skill_id)
            if resp.success:
                ok += 1
            else:
                fail += 1
                st.caption(f"Failed for {u['email']}: {resp.error}")
        prog.empty()

        st.success(f"Removed from {ok} users.")
        if fail:
            st.warning(f"{fail} failed.")

    def _page_export(self) -> None:
        st.markdown("## Export Skills")
        skills = self._ensure_skills()
        if not skills:
            return

        df = pd.DataFrame(
            [
                {
                    "Name": s.get("name", ""),
                    "State": s.get("state", ""),
                    "ID": s.get("id", ""),
                }
                for s in skills
            ]
        )

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "Download CSV",
                data=df.to_csv(index=False),
                file_name="skills.csv",
                mime="text/csv",
                use_container_width=True,
                key="sm_dl_csv",
            )
        with c2:
            st.download_button(
                "Download JSON",
                data=df.to_json(orient="records", indent=2),
                file_name="skills.json",
                mime="application/json",
                use_container_width=True,
                key="sm_dl_json",
            )

        st.markdown("### Preview")
        st.dataframe(df, use_container_width=True, hide_index=True)
