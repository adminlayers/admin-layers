"""
Group Manager Utility
Manage group membership in Genesys Cloud.
NiceGUI/Quasar implementation with clickable tables.
"""

from typing import Dict, List

from nicegui import ui

from .base import BaseUtility, UtilityConfig


class GroupManagerUtility(BaseUtility):

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="group_manager",
            name="Group Manager",
            description="View and manage group membership",
            icon="group",
            category="Users & Groups",
            requires_group=True,
            tags=["groups", "users", "membership", "bulk"],
        )

    def init_state(self) -> None:
        for key, default in [('page', 'list'), ('group_id', ''),
                             ('group_info', None), ('members', []),
                             ('list_page_size', 25), ('list_page_number', 1)]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        group_info = self.get_state('group_info')
        if group_info:
            ui.label(f"Selected: {group_info.get('name', '')}").classes(
                'text-caption text-grey-6 q-px-md')

        self.nav_button('All Groups', 'list', icon='list')
        self.nav_button('Create Group', 'create', icon='add')

        if group_info:
            self.nav_button('Members', 'detail', icon='group')
            self.nav_button('Add Members', 'add', icon='person_add')
            self.nav_button('Remove Members', 'remove', icon='person_remove')
            self.nav_button('Edit Group', 'edit', icon='edit')
            self.nav_button('Delete Group', 'delete', icon='delete')
            self.nav_button('Export', 'export', icon='download')

    def render_main(self) -> None:
        self.init_state()
        page = self.get_state('page', 'list')
        {
            'list': self._page_list, 'detail': self._page_detail,
            'add': self._page_add, 'remove': self._page_remove,
            'export': self._page_export, 'create': self._page_create,
            'edit': self._page_edit, 'delete': self._page_delete,
        }.get(page, self._page_list)()

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
            self._refresh()
        else:
            ui.notify(f'Failed to load group: {resp.error}', type='negative')

    def _refresh_members(self) -> None:
        gid = self.get_state('group_id')
        if gid:
            self.set_state('members', self.api.groups.get_members(gid))

    def _group_header(self) -> None:
        info = self.get_state('group_info')
        members = self.get_state('members', [])
        self.back_button('Back to Groups')
        self.section_title(
            info.get('name', 'Group'),
            f"{len(members)} members | {info.get('type', 'N/A')} | {info.get('visibility', 'N/A')}"
        )
        desc = info.get('description', '')
        if desc:
            ui.label(desc).classes('text-caption text-grey-6')

        with ui.row().classes('q-gutter-sm q-my-sm'):
            ui.button('Add', icon='person_add',
                      on_click=lambda: self.navigate('add')).props('flat dense no-caps')
            ui.button('Remove', icon='person_remove',
                      on_click=lambda: self.navigate('remove')).props('flat dense no-caps')
            ui.button('Export', icon='download',
                      on_click=lambda: self.navigate('export')).props('flat dense no-caps')
            ui.button('Edit', icon='edit',
                      on_click=lambda: self.navigate('edit')).props('flat dense no-caps')
            ui.button('Refresh', icon='refresh', on_click=lambda: (
                self._refresh_members(), self._refresh()
            )).props('flat dense no-caps')
        ui.separator()

    # -- pages --

    def _page_list(self) -> None:
        self.section_title('Groups')

        page_size = self.get_state('list_page_size', 25)
        page_number = self.get_state('list_page_number', 1)

        resp = self.api.groups.list_page(page_size=page_size, page_number=page_number)
        if not resp.success:
            ui.notify(f'Failed to load groups: {resp.error}', type='negative')
            return

        data = resp.data or {}
        all_groups = data.get('entities', [])
        total = data.get('total', len(all_groups))
        page_count = data.get('pageCount', 1)

        if not all_groups:
            ui.label('No groups found in your org.').classes('text-grey-6')
            return

        ui.label(f'Showing {len(all_groups)} of {total} groups (Page {page_number} of {page_count})').classes(
            'text-caption text-grey-6')

        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'members', 'label': 'Members', 'field': 'members', 'sortable': True},
            {'name': 'type', 'label': 'Type', 'field': 'type', 'sortable': True},
            {'name': 'visibility', 'label': 'Visibility', 'field': 'visibility', 'sortable': True},
        ]
        rows = [{
            'id': g.get('id', ''),
            'name': g.get('name', ''),
            'members': g.get('memberCount', 0),
            'type': g.get('type', ''),
            'visibility': g.get('visibility', ''),
        } for g in all_groups]

        self.make_table(
            columns, rows,
            on_row_click=lambda row: self._load_group(row['id']),
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

    def _page_create(self) -> None:
        self.section_title('Create Group')
        ui.label('Creating a group affects your org immediately.').classes(
            'text-caption text-amber')

        name = ui.input('Name', placeholder='Group name').classes('w-full')
        description = ui.textarea('Description', placeholder='Group description').classes('w-full')
        group_type = ui.select(['official', 'custom'], value='official', label='Type').classes('w-full')
        visibility = ui.select(['public', 'members'], value='public', label='Visibility').classes('w-full')
        confirm = ui.checkbox('I confirm I want to create this group')

        def do_create():
            if not confirm.value:
                ui.notify('Confirmation required', type='warning')
                return
            if not name.value:
                ui.notify('Group name is required', type='warning')
                return
            resp = self.api.groups.create(
                name=name.value, description=description.value,
                group_type=group_type.value, visibility=visibility.value)
            if resp.success:
                ui.notify('Group created', type='positive')
                self.set_state('group_id', resp.data.get('id'))
                self.set_state('group_info', resp.data)
                self.navigate('detail')
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Create Group', icon='add', on_click=do_create).props(
            'color=primary no-caps').classes('q-mt-md')

    def _page_edit(self) -> None:
        info = self.get_state('group_info')
        if not info:
            self.navigate('list')
            return
        self._group_header()
        self.section_title('Edit Group')

        name = ui.input('Name', value=info.get('name', '')).classes('w-full')
        description = ui.textarea('Description', value=info.get('description', '')).classes('w-full')
        visibility = ui.select(
            ['public', 'members'],
            value=info.get('visibility', 'public'),
            label='Visibility',
        ).classes('w-full')

        def do_save():
            payload = {'name': name.value, 'description': description.value, 'visibility': visibility.value}
            resp = self.api.groups.update(info.get('id'), payload)
            if resp.success:
                ui.notify('Group updated', type='positive')
                self._load_group(info.get('id'))
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Save Changes', icon='save', on_click=do_save).props(
            'color=primary no-caps').classes('q-mt-md')

    def _page_delete(self) -> None:
        info = self.get_state('group_info')
        if not info:
            self.navigate('list')
            return
        self._group_header()
        self.section_title('Delete Group')
        ui.label('Deleting a group is permanent.').classes('text-caption text-amber')
        confirm = ui.checkbox('I understand this will delete the group')

        def do_delete():
            if not confirm.value:
                ui.notify('Confirmation required', type='warning')
                return
            resp = self.api.groups.delete(info.get('id'))
            if resp.success:
                ui.notify('Group deleted', type='positive')
                self.set_state('group_info', None)
                self.set_state('group_id', '')
                self.navigate('list')
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Delete Group', icon='delete', on_click=do_delete).props(
            'color=red no-caps').classes('q-mt-md')

    def _page_detail(self) -> None:
        info = self.get_state('group_info')
        if not info:
            self.navigate('list')
            return
        self._group_header()

        members = self.get_state('members', [])
        if not members:
            ui.label('This group has no members.').classes('text-grey-6')
            return

        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'email', 'label': 'Email', 'field': 'email', 'sortable': True, 'align': 'left'},
            {'name': 'department', 'label': 'Department', 'field': 'department', 'sortable': True},
        ]
        rows = [{
            'id': m.get('id', ''),
            'name': m.get('name', ''),
            'email': m.get('email', ''),
            'department': m.get('department', ''),
        } for m in members]

        self.make_table(columns, rows, title=f'{len(members)} members')

    def _page_add(self) -> None:
        info = self.get_state('group_info')
        if not info:
            self.navigate('list')
            return
        self._group_header()
        self.section_title('Add Members')

        emails_input = ui.textarea(
            'Emails (one per line)',
            placeholder='alice@company.com\nbob@company.com',
        ).classes('w-full').style('min-height:150px')

        dry_run = ui.checkbox('Preview only (dry run)', value=True)

        def do_process():
            self._execute_add(emails_input.value or '', dry_run.value)

        ui.button('Process', icon='play_arrow', on_click=do_process).props(
            'color=primary no-caps').classes('q-mt-sm')

    def _execute_add(self, raw: str, dry_run: bool) -> None:
        emails = list(dict.fromkeys(
            e.strip() for e in raw.split('\n') if e.strip() and '@' in e
        ))
        if not emails:
            ui.notify('No valid email addresses found', type='warning')
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
            ui.notify(f'Dry run: {len(found)} users would be added', type='info')
            return

        resp = self.api.groups.add_members(self.get_state('group_id'), [u['id'] for u in found])
        if resp.success:
            ui.notify(f'Added {len(found)} members', type='positive')
            self._refresh_members()
        else:
            ui.notify(f'Failed: {resp.error}', type='negative')

    def _page_remove(self) -> None:
        info = self.get_state('group_info')
        if not info:
            self.navigate('list')
            return
        self._group_header()
        self.section_title('Remove Members')

        members = self.get_state('members', [])
        if not members:
            ui.label('No members to remove.').classes('text-grey-6')
            return

        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'email', 'label': 'Email', 'field': 'email', 'sortable': True, 'align': 'left'},
        ]
        rows = [{
            'id': m.get('id', ''),
            'name': m.get('name', ''),
            'email': m.get('email', ''),
        } for m in members]

        table = ui.table(
            columns=columns, rows=rows, row_key='id',
            selection='multiple',
            pagination={'rowsPerPage': 25},
            title='Select members to remove',
        ).classes('w-full')
        table.props('flat bordered dense')
        table.add_slot('top-right', '''
            <q-input borderless dense debounce="300" v-model="props.filter" placeholder="Search...">
                <template v-slot:append><q-icon name="search" /></template>
            </q-input>
        ''')
        table.props('filter=""')

        confirm = ui.checkbox('I confirm this removal')

        def do_remove():
            if not confirm.value:
                ui.notify('Confirmation required', type='warning')
                return
            selected = table.selected
            if not selected:
                ui.notify('No members selected', type='warning')
                return
            ids = [s['id'] for s in selected]
            resp = self.api.groups.remove_members(self.get_state('group_id'), ids)
            if resp.success:
                ui.notify(f'Removed {len(ids)} members', type='positive')
                self._refresh_members()
                self._refresh()
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Remove Selected', icon='delete', on_click=do_remove).props(
            'color=red no-caps').classes('q-mt-sm')

    def _page_export(self) -> None:
        info = self.get_state('group_info')
        if not info:
            self.navigate('list')
            return
        self._group_header()
        self.section_title('Export')

        members = self.get_state('members', [])
        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'email', 'label': 'Email', 'field': 'email', 'sortable': True, 'align': 'left'},
            {'name': 'department', 'label': 'Department', 'field': 'department', 'sortable': True},
            {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
        ]
        rows = [{
            'id': m.get('id', ''),
            'name': m.get('name', ''),
            'email': m.get('email', ''),
            'department': m.get('department', ''),
        } for m in members]

        name = info.get('name', 'group')

        csv_lines = ['Name,Email,Department,ID']
        for r in rows:
            csv_lines.append(f"{r['name']},{r['email']},{r['department']},{r['id']}")
        csv_data = '\n'.join(csv_lines)

        emails_data = '\n'.join(r['email'] for r in rows if r['email'])

        with ui.row().classes('q-gutter-sm q-mb-md'):
            ui.button('Download CSV', icon='download',
                      on_click=lambda: ui.download(csv_data.encode(),
                                                    f'{name}_members.csv')).props('no-caps')
            ui.button('Download Emails', icon='email',
                      on_click=lambda: ui.download(emails_data.encode(),
                                                    f'{name}_emails.txt')).props('no-caps outline')

        self.make_table(columns, rows, title=f'{len(rows)} members')
