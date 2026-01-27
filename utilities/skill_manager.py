"""
Skill Manager Utility
Bulk skill assignment and management for Genesys Cloud.
NiceGUI/Quasar implementation with clickable tables.
"""

import json
from typing import Dict, List, Optional

from nicegui import ui

from .base import BaseUtility, UtilityConfig


class SkillManagerUtility(BaseUtility):

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="skill_manager",
            name="Skill Manager",
            description="Bulk skill assignment and user skill lookup",
            icon="psychology",
            category="Routing",
            requires_user=False,
            tags=["skills", "routing", "users", "bulk", "assignment"],
        )

    def init_state(self) -> None:
        for key, default in [('page', 'list'), ('skills', []),
                             ('selected_skill', None), ('selected_users', []),
                             ('skill_id', ''), ('skill_info', None),
                             ('list_page_size', 25), ('list_page_number', 1)]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        skills = self.get_state('skills', [])
        if skills:
            ui.label(f'{len(skills)} skills loaded').classes(
                'text-caption text-grey-6 q-px-md')

        self.nav_button('All Skills', 'list', icon='list')
        self.nav_button('Create Skill', 'create', icon='add')
        self.nav_button('User Skills', 'user_skills', icon='person')
        self.nav_button('Bulk Assign', 'assign', icon='person_add')
        self.nav_button('Bulk Remove', 'remove', icon='person_remove')
        self.nav_button('Export', 'export', icon='download')

        skill_info = self.get_state('skill_info')
        if skill_info:
            self.nav_button('Skill Details', 'detail', icon='info')
            self.nav_button('Edit Skill', 'edit', icon='edit')
            self.nav_button('Delete Skill', 'delete', icon='delete')

    def render_main(self) -> None:
        self.init_state()
        page = self.get_state('page', 'list')
        {
            'list': self._page_list, 'user_skills': self._page_user_skills,
            'assign': self._page_assign, 'remove': self._page_remove,
            'export': self._page_export, 'create': self._page_create,
            'detail': self._page_detail, 'edit': self._page_edit,
            'delete': self._page_delete,
        }.get(page, self._page_list)()

    # -- helpers --

    def _load_skill(self, skill_id: str) -> None:
        resp = self.api.routing.get_skill(skill_id)
        if resp.success:
            self.set_state('skill_id', skill_id)
            self.set_state('skill_info', resp.data)
            self.set_state('page', 'detail')
            self._refresh()
        else:
            ui.notify(f'Failed to load skill: {resp.error}', type='negative')

    def _skill_header(self) -> None:
        info = self.get_state('skill_info')
        if not info:
            return
        self.back_button('Back to Skills')
        self.section_title(info.get('name', 'Skill'))

        with ui.row().classes('q-gutter-sm items-center'):
            state = info.get('state', 'N/A')
            color = 'green' if state == 'active' else 'grey'
            ui.badge(state, color=color).props('outline')
            ui.label(f"ID: {info.get('id', '')}").classes('text-caption text-grey-6')

        if info.get('description'):
            ui.label(info['description']).classes('text-caption text-grey-6')

        with ui.row().classes('q-gutter-sm q-my-sm'):
            ui.button('Edit', icon='edit',
                      on_click=lambda: self.navigate('edit')).props('flat dense no-caps')
            ui.button('Refresh', icon='refresh',
                      on_click=lambda: self._load_skill(info.get('id'))).props('flat dense no-caps')
        ui.separator()

    def _load_skills(self) -> List[Dict]:
        try:
            skills = self.api.routing.get_skills()
            self.set_state('skills', skills)
            return skills
        except Exception as e:
            ui.notify(f'Failed to load skills: {e}', type='negative')
            return []

    def _ensure_skills(self) -> List[Dict]:
        skills = self.get_state('skills', [])
        if not skills:
            skills = self._load_skills()
        return skills

    # -- pages --

    def _page_list(self) -> None:
        self.section_title('Skills')

        page_size = self.get_state('list_page_size', 25)
        page_number = self.get_state('list_page_number', 1)

        resp = self.api.routing.list_skills_page(page_size=page_size, page_number=page_number)
        if not resp.success:
            ui.notify(f'Failed to load skills: {resp.error}', type='negative')
            return

        data = resp.data or {}
        skills = data.get('entities', [])
        total = data.get('total', len(skills))
        page_count = data.get('pageCount', 1)

        if not skills:
            ui.label('No skills found in your org.').classes('text-grey-6')
            return

        active = sum(1 for s in skills if s.get('state') == 'active')
        ui.label(f'{len(skills)} skills ({active} active) | Page {page_number} of {page_count} | Total: {total}').classes(
            'text-caption text-grey-6')

        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'state', 'label': 'State', 'field': 'state', 'sortable': True},
        ]
        rows = [{
            'id': s.get('id', ''),
            'name': s.get('name', ''),
            'state': s.get('state', ''),
        } for s in skills]

        self.make_table(
            columns, rows,
            on_row_click=lambda row: self._load_skill(row['id']),
            title='Click a row to open',
        )

        with ui.row().classes('q-gutter-sm q-mt-md items-center'):
            ui.button('Prev', icon='chevron_left',
                      on_click=lambda: self._change_page(page_number - 1)).props(
                'flat dense no-caps').set_enabled(page_number > 1)
            ui.label(f'Page {page_number} of {page_count}').classes('text-body2')
            ui.button('Next', icon='chevron_right',
                      on_click=lambda: self._change_page(page_number + 1)).props(
                'flat dense no-caps').set_enabled(page_number < page_count)

    def _change_page(self, page: int) -> None:
        self.set_state('list_page_number', page)
        self._refresh()

    def _page_detail(self) -> None:
        info = self.get_state('skill_info')
        if not info:
            self.navigate('list')
            return
        self._skill_header()

        ui.label('Details').classes('text-h6 q-mt-md')
        for label, value in [
            ('ID', info.get('id')),
            ('Name', info.get('name')),
            ('State', info.get('state')),
            ('Description', info.get('description')),
        ]:
            self.info_row(label, value or '\u2014')

        with ui.expansion('Raw JSON').classes('q-mt-md'):
            ui.code(json.dumps(info, indent=2, default=str)).classes('w-full')

    def _page_create(self) -> None:
        self.section_title('Create Skill')
        ui.label('Creating a skill affects routing.').classes('text-caption text-amber')

        name = ui.input('Name', placeholder='Skill name').classes('w-full')
        description = ui.textarea('Description', placeholder='Skill description').classes('w-full')
        state = ui.select(['active', 'inactive'], value='active', label='State').classes('w-full')
        confirm = ui.checkbox('I confirm I want to create this skill')

        def do_create():
            if not confirm.value:
                ui.notify('Confirmation required', type='warning')
                return
            if not name.value:
                ui.notify('Skill name is required', type='warning')
                return
            resp = self.api.routing.create_skill(
                name=name.value, description=description.value, state=state.value)
            if resp.success:
                ui.notify('Skill created', type='positive')
                self.set_state('skills', [])
                self.set_state('skill_id', resp.data.get('id'))
                self.set_state('skill_info', resp.data)
                self.navigate('detail')
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Create Skill', icon='add', on_click=do_create).props(
            'color=primary no-caps').classes('q-mt-md')

    def _page_edit(self) -> None:
        info = self.get_state('skill_info')
        if not info:
            self.navigate('list')
            return
        self._skill_header()
        self.section_title('Edit Skill')

        name = ui.input('Name', value=info.get('name', '')).classes('w-full')
        description = ui.textarea('Description', value=info.get('description', '')).classes('w-full')
        state = ui.select(
            ['active', 'inactive'],
            value=info.get('state', 'active'),
            label='State',
        ).classes('w-full')

        def do_save():
            payload = {'name': name.value, 'description': description.value, 'state': state.value}
            resp = self.api.routing.update_skill(info.get('id'), payload)
            if resp.success:
                ui.notify('Skill updated', type='positive')
                self.set_state('skills', [])
                self._load_skill(info.get('id'))
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Save Changes', icon='save', on_click=do_save).props(
            'color=primary no-caps').classes('q-mt-md')

    def _page_delete(self) -> None:
        info = self.get_state('skill_info')
        if not info:
            self.navigate('list')
            return
        self._skill_header()
        self.section_title('Delete Skill')
        ui.label('Deleting a skill is permanent.').classes('text-caption text-amber')
        confirm = ui.checkbox('I understand this will delete the skill')

        def do_delete():
            if not confirm.value:
                ui.notify('Confirmation required', type='warning')
                return
            resp = self.api.routing.delete_skill(info.get('id'))
            if resp.success:
                ui.notify('Skill deleted', type='positive')
                self.set_state('skills', [])
                self.set_state('skill_info', None)
                self.set_state('skill_id', '')
                self.navigate('list')
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Delete Skill', icon='delete', on_click=do_delete).props(
            'color=red no-caps').classes('q-mt-md')

    def _page_user_skills(self) -> None:
        self.section_title('User Skills Lookup')

        with ui.row().classes('w-full q-gutter-sm items-end'):
            user_input = ui.input(
                'User email or ID', placeholder='user@example.com',
            ).classes('col-grow')

            def do_lookup():
                val = user_input.value
                if not val:
                    return
                self._lookup_user_skills(val)

            ui.button('Lookup', icon='search', on_click=do_lookup).props(
                'color=primary no-caps')

        user_info = self.get_state('current_user_info')
        user_skills = self.get_state('current_user_skills', [])

        if user_info:
            ui.separator().classes('q-my-md')
            self.section_title(
                user_info.get('name', 'Unknown'),
                f"{len(user_skills)} skill(s) | {user_info.get('email', '')} | ID: {user_info.get('id', '')}"
            )

            if user_skills:
                columns = [
                    {'name': 'name', 'label': 'Skill', 'field': 'name', 'sortable': True, 'align': 'left'},
                    {'name': 'proficiency', 'label': 'Proficiency', 'field': 'proficiency', 'sortable': True},
                    {'name': 'state', 'label': 'State', 'field': 'state', 'sortable': True},
                ]
                rows = [{
                    'id': s.get('id', ''),
                    'name': s.get('name', ''),
                    'proficiency': s.get('proficiency', 0),
                    'state': s.get('state', ''),
                } for s in user_skills]
                self.make_table(columns, rows)
            else:
                ui.label('No skills assigned to this user.').classes('text-grey-6')

    def _lookup_user_skills(self, user_input: str) -> None:
        user = None
        if '@' in user_input:
            user = self.api.users.search_by_email(user_input)
        else:
            resp = self.api.users.get(user_input)
            if resp.success:
                user = resp.data

        if not user:
            ui.notify('User not found', type='negative')
            self.set_state('current_user_info', None)
            self.set_state('current_user_skills', [])
            self._refresh()
            return

        self.set_state('current_user_info', user)
        user_skills = self.api.routing.get_user_skills(user['id'])
        self.set_state('current_user_skills', user_skills)
        self._refresh()

    def _page_assign(self) -> None:
        self.section_title('Bulk Assign Skill')
        skills = self._ensure_skills()
        if not skills:
            ui.label('No skills available.').classes('text-grey-6')
            return

        skill_map = {s.get('name', ''): s.get('id') for s in skills}
        skill_select = ui.select(
            list(skill_map.keys()),
            label='Skill to assign',
        ).classes('w-full')

        proficiency = ui.slider(min=0, max=5, step=0.5, value=3).props('label-always')
        ui.label('Proficiency').classes('text-caption text-grey-6')

        ui.separator().classes('q-my-md')

        emails_input = ui.textarea(
            'Emails (one per line)',
            placeholder='user1@company.com\nuser2@company.com',
        ).classes('w-full').style('min-height:150px')

        dry_run = ui.checkbox('Preview only (dry run)', value=True)

        def do_process():
            if not skill_select.value:
                ui.notify('Select a skill first', type='warning')
                return
            skill_id = skill_map[skill_select.value]
            self._execute_assign(
                emails_input.value or '', skill_id, skill_select.value,
                proficiency.value, dry_run.value)

        ui.button('Process', icon='play_arrow', on_click=do_process).props(
            'color=primary no-caps').classes('q-mt-sm')

    def _execute_assign(self, raw: str, skill_id: str, skill_name: str,
                        proficiency: float, dry_run: bool) -> None:
        emails = list(dict.fromkeys(
            e.strip() for e in raw.split('\n') if e.strip() and '@' in e
        ))
        if not emails:
            ui.notify('No valid emails found', type='warning')
            return

        found, missing = [], []
        for email in emails:
            user = self.api.users.search_by_email(email)
            if user:
                found.append({'id': user['id'], 'name': user.get('name', ''), 'email': email})
            else:
                missing.append(email)

        ui.notify(f'{len(found)} found, {len(missing)} not found', type='info')

        if found:
            columns = [
                {'name': 'name', 'label': 'Name', 'field': 'name', 'align': 'left'},
                {'name': 'email', 'label': 'Email', 'field': 'email', 'align': 'left'},
            ]
            self.make_table(columns, found, title=f'{len(found)} users found')

        if missing:
            with ui.column().classes('q-mt-sm'):
                ui.label(f'{len(missing)} not found:').classes('text-caption text-red')
                for e in missing:
                    ui.label(f'  {e}').classes('text-caption text-grey-6')

        if not found:
            return
        if dry_run:
            ui.notify(
                f"Dry run: would assign '{skill_name}' (proficiency {proficiency}) to {len(found)} users",
                type='info')
            return

        ui.label(f"Assigning: {skill_name} (proficiency {proficiency})").classes(
            'text-body2 q-mt-md')
        ok, fail = 0, 0
        for u in found:
            resp = self.api.routing.add_user_skill(u['id'], skill_id, proficiency)
            if resp.success:
                ok += 1
            else:
                fail += 1

        ui.notify(f'Assigned to {ok} users. {fail} failed.' if fail else f'Assigned to {ok} users.',
                  type='positive' if not fail else 'warning')

    def _page_remove(self) -> None:
        self.section_title('Bulk Remove Skill')
        skills = self._ensure_skills()
        if not skills:
            ui.label('No skills available.').classes('text-grey-6')
            return

        skill_map = {s.get('name', ''): s.get('id') for s in skills}
        skill_select = ui.select(
            list(skill_map.keys()),
            label='Skill to remove',
        ).classes('w-full')

        ui.separator().classes('q-my-md')

        emails_input = ui.textarea(
            'User emails (one per line)',
            placeholder='user1@company.com\nuser2@company.com',
        ).classes('w-full').style('min-height:150px')

        dry_run = ui.checkbox('Preview only (dry run)', value=True)
        confirm = ui.checkbox('I confirm removal')

        def do_process():
            if not skill_select.value:
                ui.notify('Select a skill first', type='warning')
                return
            if not dry_run.value and not confirm.value:
                ui.notify('Confirmation required', type='warning')
                return
            skill_id = skill_map[skill_select.value]
            self._execute_remove(
                emails_input.value or '', skill_id, skill_select.value, dry_run.value)

        ui.button('Remove Skill', icon='delete', on_click=do_process).props(
            'color=red no-caps').classes('q-mt-sm')

    def _execute_remove(self, raw: str, skill_id: str, skill_name: str, dry_run: bool) -> None:
        emails = list(dict.fromkeys(
            e.strip() for e in raw.split('\n') if e.strip() and '@' in e
        ))
        if not emails:
            ui.notify('No valid emails found', type='warning')
            return

        found, missing = [], []
        for email in emails:
            user = self.api.users.search_by_email(email)
            if user:
                found.append({'id': user['id'], 'name': user.get('name', ''), 'email': email})
            else:
                missing.append(email)

        ui.notify(f'{len(found)} found, {len(missing)} not found', type='info')

        if not found:
            return
        if dry_run:
            ui.notify(f"Dry run: would remove '{skill_name}' from {len(found)} users", type='info')
            return

        ok, fail = 0, 0
        for u in found:
            resp = self.api.routing.remove_user_skill(u['id'], skill_id)
            if resp.success:
                ok += 1
            else:
                fail += 1

        ui.notify(f'Removed from {ok} users. {fail} failed.' if fail else f'Removed from {ok} users.',
                  type='positive' if not fail else 'warning')

    def _page_export(self) -> None:
        self.section_title('Export Skills')
        skills = self._ensure_skills()
        if not skills:
            ui.label('No skills available.').classes('text-grey-6')
            return

        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'state', 'label': 'State', 'field': 'state', 'sortable': True},
            {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
        ]
        rows = [{
            'id': s.get('id', ''),
            'name': s.get('name', ''),
            'state': s.get('state', ''),
        } for s in skills]

        csv_lines = ['Name,State,ID']
        for r in rows:
            csv_lines.append(f"{r['name']},{r['state']},{r['id']}")
        csv_data = '\n'.join(csv_lines)

        json_data = json.dumps(rows, indent=2)

        with ui.row().classes('q-gutter-sm q-mb-md'):
            ui.button('Download CSV', icon='download',
                      on_click=lambda: ui.download(csv_data.encode(),
                                                    'skills.csv')).props('no-caps')
            ui.button('Download JSON', icon='download',
                      on_click=lambda: ui.download(json_data.encode(),
                                                    'skills.json')).props('no-caps outline')

        self.make_table(columns, rows, title=f'{len(rows)} skills')
