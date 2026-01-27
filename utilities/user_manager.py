"""
User Manager Utility
Search and view user details, groups, skills, and queues.
NiceGUI/Quasar implementation with clickable tables.
"""

import json
from typing import Dict, List, Optional

from nicegui import ui

from .base import BaseUtility, UtilityConfig


class UserManagerUtility(BaseUtility):

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="user_manager",
            name="User Manager",
            description="Search users and view details, groups, skills, and queues",
            icon="person",
            category="Users & Groups",
            requires_user=True,
            tags=["users", "search", "details", "groups", "skills", "queues"],
        )

    def init_state(self) -> None:
        for key, default in [('page', 'list'), ('user_info', None),
                             ('user_id', ''), ('all_users', None),
                             ('list_page_size', 25), ('list_page_number', 1)]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        user_info = self.get_state('user_info')
        if user_info:
            ui.label(f"Selected: {user_info.get('name', '')}").classes(
                'text-caption text-grey-6 q-px-md')

        self.nav_button('All Users', 'list', icon='list')
        self.nav_button('Search', 'search', icon='search')

        if user_info:
            self.nav_button('Details', 'detail', icon='info')
            self.nav_button('Edit Details', 'edit', icon='edit')
            self.nav_button('Groups', 'groups', icon='group')
            self.nav_button('Skills', 'skills', icon='psychology')
            self.nav_button('Queues', 'queues', icon='phone_in_talk')

    def render_main(self) -> None:
        self.init_state()
        page = self.get_state('page', 'list')
        {
            'list': self._page_list, 'search': self._page_search,
            'detail': self._page_detail, 'groups': self._page_groups,
            'skills': self._page_skills, 'queues': self._page_queues,
            'edit': self._page_edit,
        }.get(page, self._page_list)()

    # -- helpers --

    def _load_user(self, user_id: str) -> None:
        if not user_id:
            return
        resp = self.api.users.get(user_id)
        if resp.success:
            self.set_state('user_id', user_id)
            self.set_state('user_info', resp.data)
            self.set_state('page', 'detail')
            self._refresh()
        else:
            ui.notify(f'User not found: {resp.error}', type='negative')

    def _load_user_by_email(self, email: str) -> None:
        user = self.api.users.search_by_email(email)
        if user:
            self.set_state('user_id', user['id'])
            self.set_state('user_info', user)
            self.set_state('page', 'detail')
            self._refresh()
        else:
            ui.notify(f'No user found with email: {email}', type='negative')

    def _clear_user(self) -> None:
        self.set_state('user_id', '')
        self.set_state('user_info', None)
        self.navigate('list')

    def _user_header(self) -> None:
        info = self.get_state('user_info')
        if not info:
            return
        self.back_button('Back to Users')
        self.section_title(info.get('name', 'User'))

        parts = [info.get('state', 'N/A')]
        if info.get('email'):
            parts.append(info['email'])
        if info.get('department'):
            parts.append(info['department'])
        if info.get('title'):
            parts.append(info['title'])
        ui.label(' | '.join(parts)).classes('text-caption text-grey-6')

        with ui.row().classes('q-gutter-sm q-my-sm'):
            ui.button('Groups', icon='group',
                      on_click=lambda: self.navigate('groups')).props('flat dense no-caps')
            ui.button('Skills', icon='psychology',
                      on_click=lambda: self.navigate('skills')).props('flat dense no-caps')
            ui.button('Queues', icon='phone_in_talk',
                      on_click=lambda: self.navigate('queues')).props('flat dense no-caps')
            ui.button('Edit', icon='edit',
                      on_click=lambda: self.navigate('edit')).props('flat dense no-caps')
            ui.button('Refresh', icon='refresh',
                      on_click=lambda: self._load_user(self.get_state('user_id'))).props('flat dense no-caps')
        ui.separator()

    # -- pages --

    def _page_list(self) -> None:
        self.section_title('Users')

        page_size = self.get_state('list_page_size', 25)
        page_number = self.get_state('list_page_number', 1)

        resp = self.api.users.list_page(page_size=page_size, page_number=page_number)
        if not resp.success:
            ui.notify(f'Failed to load users: {resp.error}', type='negative')
            return

        data = resp.data or {}
        all_users = data.get('entities', [])
        total = data.get('total', len(all_users))
        page_count = data.get('pageCount', 1)

        if not all_users:
            ui.label('No users found in your org.').classes('text-grey-6')
            return

        ui.label(f'Showing {len(all_users)} of {total} users (Page {page_number} of {page_count})').classes(
            'text-caption text-grey-6')

        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'email', 'label': 'Email', 'field': 'email', 'sortable': True, 'align': 'left'},
            {'name': 'department', 'label': 'Department', 'field': 'department', 'sortable': True},
            {'name': 'title', 'label': 'Title', 'field': 'title', 'sortable': True},
            {'name': 'state', 'label': 'State', 'field': 'state', 'sortable': True},
        ]
        rows = [{
            'id': u.get('id', ''),
            'name': u.get('name', ''),
            'email': u.get('email', ''),
            'department': u.get('department', ''),
            'title': u.get('title', ''),
            'state': u.get('state', ''),
        } for u in all_users]

        self.make_table(
            columns, rows,
            on_row_click=lambda row: self._load_user(row['id']),
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

        # Export
        csv_lines = ['Name,Email,Department,Title,State,ID']
        for r in rows:
            csv_lines.append(f"{r['name']},{r['email']},{r['department']},{r['title']},{r['state']},{r['id']}")
        csv_data = '\n'.join(csv_lines)

        ui.button('Export CSV', icon='download',
                  on_click=lambda: ui.download(csv_data.encode(), 'users.csv')).props(
            'flat no-caps').classes('q-mt-sm')

    def _change_page(self, page: int) -> None:
        self.set_state('list_page_number', page)
        self._refresh()

    def _page_search(self) -> None:
        self.section_title('Search Users')

        with ui.row().classes('w-full q-gutter-sm items-end'):
            search_input = ui.input(
                'Search by name or email',
                placeholder='Type a name or email address...',
            ).classes('col-grow')

            def do_search():
                query = search_input.value
                if not query:
                    return
                if '@' in query:
                    user = self.api.users.search_by_email(query)
                    results = [user] if user else []
                else:
                    results = self.api.users.search(query)
                self.set_state('search_results', results)
                self._refresh()

            ui.button('Search', icon='search', on_click=do_search).props(
                'color=primary no-caps')

        results = self.get_state('search_results', [])
        if results:
            ui.label(f'{len(results)} result(s)').classes('text-caption text-grey-6 q-mt-md')

            columns = [
                {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
                {'name': 'email', 'label': 'Email', 'field': 'email', 'sortable': True, 'align': 'left'},
                {'name': 'department', 'label': 'Department', 'field': 'department', 'sortable': True},
                {'name': 'title', 'label': 'Title', 'field': 'title', 'sortable': True},
                {'name': 'state', 'label': 'State', 'field': 'state', 'sortable': True},
            ]
            rows = [{
                'id': u.get('id', ''),
                'name': u.get('name', ''),
                'email': u.get('email', ''),
                'department': u.get('department', ''),
                'title': u.get('title', ''),
                'state': u.get('state', ''),
            } for u in results]

            self.make_table(
                columns, rows,
                on_row_click=lambda row: self._load_user(row['id']),
                title='Click a row to open',
            )

    def _page_detail(self) -> None:
        info = self.get_state('user_info')
        if not info:
            self.navigate('list')
            return

        self._user_header()

        # Stats row
        with ui.row().classes('q-gutter-md q-mb-md'):
            for label, value in [
                ('State', info.get('state', 'N/A')),
                ('Department', info.get('department', 'N/A')),
                ('Title', info.get('title', 'N/A')),
            ]:
                with ui.card().classes('q-pa-sm'):
                    ui.label(label).classes('text-caption text-grey-6 text-uppercase')
                    ui.label(value).classes('text-body1')

        # Profile details
        ui.label('Profile Details').classes('text-h6 q-mt-md')
        for label, value in [
            ('ID', info.get('id')),
            ('Email', info.get('email')),
            ('Name', info.get('name')),
            ('Department', info.get('department')),
            ('Title', info.get('title')),
            ('State', info.get('state')),
            ('Manager', info.get('manager', {}).get('name') if info.get('manager') else None),
            ('Division', info.get('division', {}).get('name') if info.get('division') else None),
        ]:
            self.info_row(label, value or '\u2014')

        # Addresses
        addresses = info.get('addresses', [])
        if addresses:
            ui.label('Contact').classes('text-h6 q-mt-md')
            for addr in addresses:
                media = addr.get('mediaType', addr.get('type', ''))
                value = addr.get('address', addr.get('display', ''))
                if media or value:
                    self.info_row(media, value)

        with ui.expansion('Raw JSON').classes('q-mt-md'):
            ui.code(json.dumps(info, indent=2, default=str)).classes('w-full')

        # Quick Actions
        ui.separator().classes('q-my-md')
        ui.label('Quick Actions').classes('text-h6')

        with ui.tabs().classes('w-full') as tabs:
            tab_group = ui.tab('Add to Group', icon='group')
            tab_skill = ui.tab('Assign Skill', icon='psychology')
            tab_queue = ui.tab('Add to Queue', icon='phone_in_talk')

        with ui.tab_panels(tabs, value=tab_group).classes('w-full'):
            with ui.tab_panel(tab_group):
                self._render_quick_group(info)
            with ui.tab_panel(tab_skill):
                self._render_quick_skill(info)
            with ui.tab_panel(tab_queue):
                self._render_quick_queue(info)

    def _render_quick_group(self, info: Dict) -> None:
        group_input = ui.input('Search groups', placeholder='Start typing a group name...').classes('w-full')
        results_area = ui.column().classes('w-full')

        def do_search():
            query = group_input.value
            if not query:
                return
            groups = self.api.groups.search(query)
            results_area.clear()
            with results_area:
                if not groups:
                    ui.label('No groups found').classes('text-grey-6')
                    return
                group_map = {g.get('name', '?'): g.get('id') for g in groups}
                group_select = ui.select(list(group_map.keys()), label='Select group').classes('w-full')
                confirm = ui.checkbox('I confirm adding this user to the group')

                def do_add():
                    if not confirm.value:
                        ui.notify('Confirmation required', type='warning')
                        return
                    if not group_select.value:
                        ui.notify('Select a group', type='warning')
                        return
                    resp = self.api.groups.add_members(group_map[group_select.value], [info['id']])
                    if resp.success:
                        ui.notify('User added to group', type='positive')
                        self.set_state('user_groups', None)
                    else:
                        ui.notify(f'Failed: {resp.error}', type='negative')

                ui.button('Add to Group', icon='group_add', on_click=do_add).props(
                    'color=primary no-caps').classes('q-mt-sm')

        group_input.on('keydown.enter', do_search)
        ui.button('Search', icon='search', on_click=do_search).props('flat dense no-caps')

    def _render_quick_skill(self, info: Dict) -> None:
        skills = self.api.routing.get_skills()
        if not skills:
            ui.label('No skills available.').classes('text-grey-6')
            return

        skill_map = {s.get('name', ''): s.get('id') for s in skills}
        skill_select = ui.select(list(skill_map.keys()), label='Select skill').classes('w-full')
        proficiency = ui.slider(min=0, max=5, step=0.5, value=3).props('label-always')
        ui.label('Proficiency').classes('text-caption text-grey-6')
        confirm = ui.checkbox('I confirm assigning this skill')

        def do_assign():
            if not confirm.value:
                ui.notify('Confirmation required', type='warning')
                return
            if not skill_select.value:
                ui.notify('Select a skill', type='warning')
                return
            resp = self.api.routing.add_user_skill(
                info['id'], skill_map[skill_select.value], proficiency.value)
            if resp.success:
                ui.notify('Skill assigned', type='positive')
                self.set_state('user_skills_list', None)
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Assign Skill', icon='psychology', on_click=do_assign).props(
            'color=primary no-caps').classes('q-mt-sm')

    def _render_quick_queue(self, info: Dict) -> None:
        queue_input = ui.input('Search queues', placeholder='Start typing a queue name...').classes('w-full')
        results_area = ui.column().classes('w-full')

        def do_search():
            query = queue_input.value
            if not query:
                return
            queues = self.api.queues.search(query)
            results_area.clear()
            with results_area:
                if not queues:
                    ui.label('No queues found').classes('text-grey-6')
                    return
                queue_map = {q.get('name', '?'): q.get('id') for q in queues}
                queue_select = ui.select(list(queue_map.keys()), label='Select queue').classes('w-full')
                confirm = ui.checkbox('I confirm adding this user to the queue')

                def do_add():
                    if not confirm.value:
                        ui.notify('Confirmation required', type='warning')
                        return
                    if not queue_select.value:
                        ui.notify('Select a queue', type='warning')
                        return
                    resp = self.api.queues.add_members(queue_map[queue_select.value], [info['id']])
                    if resp.success:
                        ui.notify('User added to queue', type='positive')
                        self.set_state('user_queues_list', None)
                    else:
                        ui.notify(f'Failed: {resp.error}', type='negative')

                ui.button('Add to Queue', icon='phone_in_talk', on_click=do_add).props(
                    'color=primary no-caps').classes('q-mt-sm')

        queue_input.on('keydown.enter', do_search)
        ui.button('Search', icon='search', on_click=do_search).props('flat dense no-caps')

    def _page_edit(self) -> None:
        info = self.get_state('user_info')
        if not info:
            self.navigate('list')
            return

        self._user_header()
        self.section_title('Edit User Details')

        name = ui.input('Name', value=info.get('name', '')).classes('w-full')
        department = ui.input('Department', value=info.get('department', '')).classes('w-full')
        title = ui.input('Title', value=info.get('title', '')).classes('w-full')
        state = ui.select(
            ['active', 'inactive'],
            value=info.get('state', 'active'),
            label='State',
        ).classes('w-full')
        confirm = ui.checkbox('I confirm updating this user')

        def do_save():
            if not confirm.value:
                ui.notify('Confirmation required', type='warning')
                return
            payload = {
                'name': name.value,
                'department': department.value,
                'title': title.value,
                'state': state.value,
            }
            resp = self.api.users.update(info['id'], payload)
            if resp.success:
                ui.notify('User updated', type='positive')
                self._load_user(info['id'])
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Save Changes', icon='save', on_click=do_save).props(
            'color=primary no-caps').classes('q-mt-md')

    def _page_groups(self) -> None:
        info = self.get_state('user_info')
        if not info:
            self.navigate('list')
            return

        self._user_header()
        self.section_title('Groups')

        groups = self.get_state('user_groups')

        if groups is None:
            resp = self.api.users.get_groups(info['id'])
            if resp.success:
                data = resp.data
                groups = data.get('entities', data) if isinstance(data, dict) else data
                if not isinstance(groups, list):
                    groups = []
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')
                groups = []
            self.set_state('user_groups', groups)

        ui.button('Refresh', icon='refresh', on_click=lambda: (
            self.set_state('user_groups', None), self._refresh()
        )).props('flat dense no-caps')

        if not groups:
            ui.label('No groups found for this user.').classes('text-grey-6')
            return

        ui.label(f'{len(groups)} group(s)').classes('text-caption text-grey-6')

        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'type', 'label': 'Type', 'field': 'type', 'sortable': True},
            {'name': 'members', 'label': 'Members', 'field': 'members', 'sortable': True},
        ]
        rows = [{
            'id': g.get('id', ''),
            'name': g.get('name', ''),
            'type': g.get('type', ''),
            'members': g.get('memberCount', ''),
        } for g in groups]

        self.make_table(columns, rows)

    def _page_skills(self) -> None:
        info = self.get_state('user_info')
        if not info:
            self.navigate('list')
            return

        self._user_header()
        self.section_title('Skills')

        skills = self.get_state('user_skills_list')

        if skills is None:
            skills = self.api.routing.get_user_skills(info['id'])
            self.set_state('user_skills_list', skills)

        ui.button('Refresh', icon='refresh', on_click=lambda: (
            self.set_state('user_skills_list', None), self._refresh()
        )).props('flat dense no-caps')

        if not skills:
            ui.label('No skills assigned to this user.').classes('text-grey-6')
            return

        ui.label(f'{len(skills)} skill(s)').classes('text-caption text-grey-6')

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
        } for s in skills]

        self.make_table(columns, rows)

    def _page_queues(self) -> None:
        info = self.get_state('user_info')
        if not info:
            self.navigate('list')
            return

        self._user_header()
        self.section_title('Queues')

        queues = self.get_state('user_queues_list')

        if queues is None:
            queues = self.api.users.get_queues(info['id'])
            self.set_state('user_queues_list', queues)

        ui.button('Refresh', icon='refresh', on_click=lambda: (
            self.set_state('user_queues_list', None), self._refresh()
        )).props('flat dense no-caps')

        if not queues:
            ui.label('No queues found for this user.').classes('text-grey-6')
            return

        ui.label(f'{len(queues)} queue(s)').classes('text-caption text-grey-6')

        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'members', 'label': 'Members', 'field': 'members', 'sortable': True},
        ]
        rows = [{
            'id': q.get('id', ''),
            'name': q.get('name', ''),
            'members': q.get('memberCount', ''),
        } for q in queues]

        self.make_table(columns, rows)
