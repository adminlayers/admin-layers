"""
Skill Manager Utility
Bulk skill assignment and management for Genesys Cloud.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional

from .base import BaseUtility, UtilityConfig


class SkillManagerUtility(BaseUtility):

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="skill_manager",
            name="Skill Manager",
            description="Bulk skill assignment and user skill lookup",
            icon="\U0001F3AF",
            category="Routing",
            requires_user=False,
            tags=["skills", "routing", "users", "bulk", "assignment"]
        )

    def init_state(self) -> None:
        for key, default in [('page', 'skills'), ('skills', []),
                             ('selected_skill', None), ('selected_users', [])]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        st.markdown("#### Skill Manager")

        if st.button("Load All Skills", use_container_width=True, key="sm_load_skills"):
            self._load_skills()

        skills = self.get_state('skills', [])
        if skills:
            st.caption(f"{len(skills)} skills loaded")

        st.markdown("---")
        st.markdown("#### Views")

        for key, icon, label, page in [
            ("sm_nav_skills", "\U0001F4CB", "All Skills", "skills"),
            ("sm_nav_user", "\U0001F464", "User Skills", "user_skills"),
            ("sm_nav_assign", "\U00002795", "Bulk Assign", "assign"),
            ("sm_nav_remove", "\U00002796", "Bulk Remove", "remove"),
            ("sm_nav_export", "\U0001F4E4", "Export", "export"),
        ]:
            if st.button(f"{icon} {label}", use_container_width=True, key=key):
                self.set_state('page', page)
                st.rerun()

    def render_main(self) -> None:
        self.init_state()
        page = self.get_state('page', 'skills')
        pages = {
            'skills': self._page_skills, 'user_skills': self._page_user_skills,
            'assign': self._page_assign, 'remove': self._page_remove,
            'export': self._page_export,
        }
        pages.get(page, self._page_skills)()

    # -- data helpers --

    def _load_skills(self) -> None:
        with st.spinner("Loading skills..."):
            try:
                skills = self.api.routing.get_skills()
                self.set_state('skills', skills)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to load skills: {e}")

    def _ensure_skills(self) -> List[Dict]:
        skills = self.get_state('skills', [])
        if not skills:
            st.warning("Click 'Load All Skills' in the sidebar first.")
        return skills

    # -- pages --

    def _page_skills(self) -> None:
        st.markdown("## Skills")
        skills = self.get_state('skills', [])

        if not skills:
            st.info("Click 'Load All Skills' in the sidebar to begin.")
            return

        c1, c2 = st.columns(2)
        c1.metric("Total Skills", len(skills))
        active = sum(1 for s in skills if s.get('state') == 'active')
        c2.metric("Active", active)

        search = st.text_input("Filter", placeholder="Search skills...", key="sm_filter")

        df = pd.DataFrame([{
            'Name': s.get('name', ''),
            'State': s.get('state', ''),
            'ID': s.get('id', ''),
        } for s in skills])

        if search and not df.empty:
            df = df[df['Name'].str.contains(search, case=False, na=False)]

        st.caption(f"Showing {len(df)} of {len(skills)} skills")
        st.dataframe(df, use_container_width=True, hide_index=True, height=min(500, 35 * len(df) + 38))

    def _page_user_skills(self) -> None:
        st.markdown("## User Skills Lookup")

        c1, c2 = st.columns([4, 1])
        with c1:
            user_input = st.text_input(
                "User email or ID", placeholder="user@example.com",
                key="sm_user_input"
            )
        with c2:
            st.markdown("")
            st.markdown("")
            lookup = st.button("Lookup", type="primary", use_container_width=True, key="sm_lookup_btn")

        if lookup and user_input:
            self._lookup_user_skills(user_input)

        user_info = self.get_state('current_user_info')
        user_skills = self.get_state('current_user_skills', [])

        if user_info:
            st.markdown("---")
            st.markdown(f"### {user_info.get('name', 'Unknown')}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Skills", len(user_skills))
            c2.caption(f"**Email:** {user_info.get('email', '')}")
            c3.caption(f"**ID:** {user_info.get('id', '')}")

            if user_skills:
                df = pd.DataFrame([{
                    'Skill': s.get('name', ''),
                    'Proficiency': s.get('proficiency', 0),
                    'State': s.get('state', ''),
                    'ID': s.get('id', ''),
                } for s in user_skills])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No skills assigned to this user.")

    def _lookup_user_skills(self, user_input: str) -> None:
        with st.spinner("Looking up user..."):
            user = None
            if '@' in user_input:
                user = self.api.users.search_by_email(user_input)
            else:
                resp = self.api.users.get(user_input)
                if resp.success:
                    user = resp.data

            if not user:
                st.error("User not found.")
                self.set_state('current_user_info', None)
                self.set_state('current_user_skills', [])
                return

            self.set_state('current_user_info', user)
            user_skills = self.api.routing.get_user_skills(user['id'])
            self.set_state('current_user_skills', user_skills)
            st.rerun()

    def _page_assign(self) -> None:
        st.markdown("## Bulk Assign Skill")
        skills = self._ensure_skills()
        if not skills:
            return

        skill_map = {s.get('name', ''): s.get('id') for s in skills}
        selected_name = st.selectbox("Skill to assign", list(skill_map.keys()), key="sm_assign_skill")

        proficiency = st.slider("Proficiency", 0.0, 5.0, 3.0, 0.5, key="sm_prof")

        st.markdown("---")

        tab1, tab2 = st.tabs(["Paste Emails", "Upload File"])
        emails_text = ""
        with tab1:
            emails_text = st.text_area(
                "Emails (one per line)", height=180,
                placeholder="user1@company.com\nuser2@company.com", key="sm_paste"
            )
        with tab2:
            uploaded = st.file_uploader("CSV or TXT", type=['csv', 'txt'], key="sm_upload")
            if uploaded:
                content = uploaded.read().decode('utf-8')
                emails_text = "\n".join(
                    line.split(',')[0].strip().strip('"')
                    for line in content.split('\n') if '@' in line
                )
                st.code(emails_text, language=None)

        c1, c2 = st.columns(2)
        dry_run = c1.checkbox("Preview only (dry run)", value=True, key="sm_dryrun")
        run = c2.button("Process", type="primary", use_container_width=True, key="sm_run_assign")

        if run and emails_text and selected_name:
            skill_id = skill_map[selected_name]
            self._execute_assign(emails_text, skill_id, selected_name, proficiency, dry_run)

    def _execute_assign(self, raw: str, skill_id: str, skill_name: str,
                        proficiency: float, dry_run: bool) -> None:
        emails = list(dict.fromkeys(
            e.strip() for e in raw.split('\n') if e.strip() and '@' in e
        ))
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
            st.info(f"Dry run: would assign '{skill_name}' (proficiency {proficiency}) to {len(found)} users.")
            return

        st.markdown("---")
        st.markdown(f"**Assigning:** {skill_name} (proficiency {proficiency})")
        prog = st.progress(0)
        ok, fail = 0, 0
        for i, u in enumerate(found):
            prog.progress((i + 1) / len(found))
            resp = self.api.routing.add_user_skill(u['id'], skill_id, proficiency)
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

        skill_map = {s.get('name', ''): s.get('id') for s in skills}
        selected_name = st.selectbox("Skill to remove", list(skill_map.keys()), key="sm_rm_skill")

        st.markdown("---")

        emails_text = st.text_area(
            "User emails (one per line)", height=180,
            placeholder="user1@company.com\nuser2@company.com", key="sm_rm_emails"
        )

        c1, c2 = st.columns(2)
        dry_run = c1.checkbox("Preview only (dry run)", value=True, key="sm_rm_dryrun")
        confirm = c2.checkbox("I confirm removal", key="sm_rm_confirm")

        if st.button("Remove Skill", type="primary",
                     disabled=not confirm and not dry_run,
                     use_container_width=True, key="sm_rm_btn"):
            if emails_text and selected_name:
                skill_id = skill_map[selected_name]
                self._execute_remove(emails_text, skill_id, selected_name, dry_run)

    def _execute_remove(self, raw: str, skill_id: str, skill_name: str, dry_run: bool) -> None:
        emails = list(dict.fromkeys(
            e.strip() for e in raw.split('\n') if e.strip() and '@' in e
        ))
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
                found.append({'id': user['id'], 'name': user.get('name', ''), 'email': email})
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
            resp = self.api.routing.remove_user_skill(u['id'], skill_id)
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

        df = pd.DataFrame([{
            'Name': s.get('name', ''),
            'State': s.get('state', ''),
            'ID': s.get('id', ''),
        } for s in skills])

        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Download CSV", data=df.to_csv(index=False),
                               file_name="skills.csv", mime="text/csv",
                               use_container_width=True, key="sm_dl_csv")
        with c2:
            st.download_button("Download JSON", data=df.to_json(orient='records', indent=2),
                               file_name="skills.json", mime="application/json",
                               use_container_width=True, key="sm_dl_json")

        st.markdown("### Preview")
        st.dataframe(df, use_container_width=True, hide_index=True)
