"""
Queue Manager Utility
View and manage queue membership in Genesys Cloud.
NiceGUI/Quasar implementation with clickable tables.
"""

import json
from typing import Dict, List, Optional

from nicegui import ui

from .base import BaseUtility, UtilityConfig


class QueueManagerUtility(BaseUtility):

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="queue_manager",
            name="Queue Manager",
            description="View and manage queue membership and configuration",
            icon="phone_in_talk",
            category="Routing",
            requires_queue=True,
            tags=["queues", "routing", "membership", "agents"],
        )

    def init_state(self) -> None:
        for key, default in [('page', 'list'), ('queue_id', ''),
                             ('queue_info', None), ('members', []),
                             ('list_page_size', 25), ('list_page_number', 1)]:
            if self.get_state(key) is None:
                self.set_state(key, default)

    def render_sidebar(self) -> None:
        queue_info = self.get_state('queue_info')
        if queue_info:
            ui.label(f"Selected: {queue_info.get('name', '')}").classes(
                'text-caption text-grey-6 q-px-md')

        self.nav_button('All Queues', 'list', icon='list')
        self.nav_button('Create Queue', 'create', icon='add')

        if queue_info:
            self.nav_button('Members', 'view', icon='group')
            self.nav_button('Add Members', 'add', icon='person_add')
            self.nav_button('Remove Members', 'remove', icon='person_remove')
            self.nav_button('Config', 'config', icon='settings')
            self.nav_button('Edit Queue', 'edit', icon='edit')
            self.nav_button('Delete Queue', 'delete', icon='delete')
            self.nav_button('Export', 'export', icon='download')

    def render_main(self) -> None:
        self.init_state()
        page = self.get_state('page', 'list')
        {
            'list': self._page_list, 'view': self._page_view,
            'add': self._page_add, 'remove': self._page_remove,
            'config': self._page_config, 'export': self._page_export,
            'create': self._page_create, 'edit': self._page_edit,
            'delete': self._page_delete,
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
            self._refresh()
        else:
            ui.notify(f'Failed to load queue: {resp.error}', type='negative')

    def _refresh_members(self) -> None:
        qid = self.get_state('queue_id')
        if qid:
            self.set_state('members', self.api.queues.get_members(qid))

    def _queue_header(self) -> None:
        info = self.get_state('queue_info')
        members = self.get_state('members', [])
        self.back_button('Back to Queues')

        acw = info.get('acwSettings', {})
        acw_timeout = acw.get('timeoutMs')
        acw_str = f"{acw_timeout // 1000}s" if acw_timeout else "N/A"
        media = info.get('mediaSettings', {})
        call_settings = media.get('call', {})
        alert = call_settings.get('alertingTimeoutSeconds')
        alert_str = f"{alert}s" if alert else "N/A"

        self.section_title(
            info.get('name', 'Queue'),
            f"{len(members)} members | Skill eval: {info.get('skillEvaluationMethod', 'N/A')} | ACW: {acw_str} | Alert: {alert_str}"
        )
        desc = info.get('description', '')
        if desc:
            ui.label(desc).classes('text-caption text-grey-6')

        with ui.row().classes('q-gutter-sm q-my-sm'):
            ui.button('Add', icon='person_add',
                      on_click=lambda: self.navigate('add')).props('flat dense no-caps')
            ui.button('Remove', icon='person_remove',
                      on_click=lambda: self.navigate('remove')).props('flat dense no-caps')
            ui.button('Config', icon='settings',
                      on_click=lambda: self.navigate('config')).props('flat dense no-caps')
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
        self.section_title('Queues')

        page_size = self.get_state('list_page_size', 25)
        page_number = self.get_state('list_page_number', 1)

        resp = self.api.queues.list_page(page_size=page_size, page_number=page_number)
        if not resp.success:
            ui.notify(f'Failed to load queues: {resp.error}', type='negative')
            return

        data = resp.data or {}
        all_queues = data.get('entities', [])
        total = data.get('total', len(all_queues))
        page_count = data.get('pageCount', 1)

        if not all_queues:
            ui.label('No queues found in your org.').classes('text-grey-6')
            return

        ui.label(f'Showing {len(all_queues)} of {total} queues (Page {page_number} of {page_count})').classes(
            'text-caption text-grey-6')

        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'members', 'label': 'Members', 'field': 'members', 'sortable': True},
            {'name': 'skill_eval', 'label': 'Skill Eval', 'field': 'skill_eval', 'sortable': True},
        ]
        rows = [{
            'id': q.get('id', ''),
            'name': q.get('name', ''),
            'members': q.get('memberCount', 0),
            'skill_eval': q.get('skillEvaluationMethod', ''),
        } for q in all_queues]

        self.make_table(
            columns, rows,
            on_row_click=lambda row: self._load_queue(row['id']),
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
        self.section_title('Create Queue')
        ui.label('Creating a queue affects routing. Confirm before creating.').classes(
            'text-caption text-amber')

        name = ui.input('Name', placeholder='Queue name').classes('w-full')
        description = ui.textarea('Description', placeholder='Queue description').classes('w-full')
        skill_eval = ui.select(['BEST', 'ALL'], value='BEST', label='Skill Evaluation').classes('w-full')
        calling_party_name = ui.input('Calling Party Name', placeholder='Outbound display name').classes('w-full')
        calling_party_number = ui.input('Calling Party Number', placeholder='+18005551234').classes('w-full')
        acw_timeout = ui.number('ACW Timeout (seconds)', value=60, min=0, step=5).classes('w-full')
        alert_timeout = ui.number('Alert Timeout (seconds)', value=30, min=0, step=5).classes('w-full')
        confirm = ui.checkbox('I confirm I want to create this queue')

        def do_create():
            if not confirm.value:
                ui.notify('Confirmation required', type='warning')
                return
            if not name.value:
                ui.notify('Queue name is required', type='warning')
                return
            payload = {
                'name': name.value,
                'description': description.value,
                'skillEvaluationMethod': skill_eval.value,
                'callingPartyName': calling_party_name.value,
                'callingPartyNumber': calling_party_number.value,
                'acwSettings': {'wrapupPrompt': 'MANDATORY', 'timeoutMs': int((acw_timeout.value or 0) * 1000)},
                'mediaSettings': {'call': {'alertingTimeoutSeconds': int(alert_timeout.value or 0)}},
            }
            resp = self.api.queues.create(payload)
            if resp.success:
                ui.notify('Queue created', type='positive')
                self.set_state('queue_id', resp.data.get('id'))
                self.set_state('queue_info', resp.data)
                self.navigate('view')
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Create Queue', icon='add', on_click=do_create).props(
            'color=primary no-caps').classes('q-mt-md')

    def _page_edit(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            self.navigate('list')
            return
        self._queue_header()
        self.section_title('Edit Queue')

        acw = info.get('acwSettings', {}) or {}
        media = info.get('mediaSettings', {}) or {}
        call_settings = media.get('call', {}) if isinstance(media, dict) else {}

        name = ui.input('Name', value=info.get('name', '')).classes('w-full')
        description = ui.textarea('Description', value=info.get('description', '')).classes('w-full')
        skill_eval = ui.select(
            ['BEST', 'ALL'],
            value=info.get('skillEvaluationMethod', 'BEST'),
            label='Skill Evaluation',
        ).classes('w-full')
        calling_party_name = ui.input('Calling Party Name',
                                       value=info.get('callingPartyName', '')).classes('w-full')
        calling_party_number = ui.input('Calling Party Number',
                                         value=info.get('callingPartyNumber', '')).classes('w-full')
        acw_timeout = ui.number('ACW Timeout (seconds)',
                                 value=int((acw.get('timeoutMs') or 60000) / 1000),
                                 min=0, step=5).classes('w-full')
        alert_timeout = ui.number('Alert Timeout (seconds)',
                                   value=int(call_settings.get('alertingTimeoutSeconds') or 30),
                                   min=0, step=5).classes('w-full')

        def do_save():
            payload = {
                'name': name.value,
                'description': description.value,
                'skillEvaluationMethod': skill_eval.value,
                'callingPartyName': calling_party_name.value,
                'callingPartyNumber': calling_party_number.value,
                'acwSettings': {
                    'wrapupPrompt': acw.get('wrapupPrompt', 'MANDATORY'),
                    'timeoutMs': int((acw_timeout.value or 0) * 1000),
                },
                'mediaSettings': {'call': {'alertingTimeoutSeconds': int(alert_timeout.value or 0)}},
            }
            resp = self.api.queues.update(info.get('id'), payload)
            if resp.success:
                ui.notify('Queue updated', type='positive')
                self._load_queue(info.get('id'))
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Save Changes', icon='save', on_click=do_save).props(
            'color=primary no-caps').classes('q-mt-md')

    def _page_delete(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            self.navigate('list')
            return
        self._queue_header()
        self.section_title('Delete Queue')
        ui.label('Deleting a queue is permanent.').classes('text-caption text-amber')
        confirm = ui.checkbox('I understand this will delete the queue')

        def do_delete():
            if not confirm.value:
                ui.notify('Confirmation required', type='warning')
                return
            resp = self.api.queues.delete(info.get('id'))
            if resp.success:
                ui.notify('Queue deleted', type='positive')
                self.set_state('queue_info', None)
                self.set_state('queue_id', '')
                self.navigate('list')
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Delete Queue', icon='delete', on_click=do_delete).props(
            'color=red no-caps').classes('q-mt-md')

    def _page_view(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            self.navigate('list')
            return
        self._queue_header()

        members = self.get_state('members', [])
        if not members:
            ui.label('This queue has no members.').classes('text-grey-6')
            return

        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'email', 'label': 'Email', 'field': 'email', 'sortable': True, 'align': 'left'},
            {'name': 'joined', 'label': 'Joined', 'field': 'joined', 'sortable': True},
        ]
        rows = [{
            'id': m.get('id', m.get('user', {}).get('id', '')),
            'name': m.get('name', m.get('user', {}).get('name', '')),
            'email': m.get('email', m.get('user', {}).get('email', '')),
            'joined': str(m.get('joined', '')),
        } for m in members]

        self.make_table(columns, rows, title=f'{len(members)} members')

    def _page_add(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            self.navigate('list')
            return
        self._queue_header()
        self.section_title('Add Members')

        emails_input = ui.textarea(
            'Emails (one per line)',
            placeholder='agent1@company.com\nagent2@company.com',
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

        resp = self.api.queues.add_members(self.get_state('queue_id'), [u['id'] for u in found])
        if resp.success:
            ui.notify(f'Added {len(found)} members', type='positive')
            self._refresh_members()
        else:
            ui.notify(f'Failed: {resp.error}', type='negative')

    def _page_remove(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            self.navigate('list')
            return
        self._queue_header()
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
            'id': m.get('id', m.get('user', {}).get('id', '')),
            'name': m.get('name', m.get('user', {}).get('name', '')),
            'email': m.get('email', m.get('user', {}).get('email', '')),
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
            resp = self.api.queues.remove_members(self.get_state('queue_id'), ids)
            if resp.success:
                ui.notify(f'Removed {len(ids)} agents from queue', type='positive')
                self._refresh_members()
                self._refresh()
            else:
                ui.notify(f'Failed: {resp.error}', type='negative')

        ui.button('Remove Selected', icon='delete', on_click=do_remove).props(
            'color=red no-caps').classes('q-mt-sm')

    def _page_config(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            self.navigate('list')
            return
        self._queue_header()
        self.section_title('Configuration')

        # General
        ui.label('General').classes('text-h6 q-mt-md')
        for label, value in [
            ('ID', info.get('id', '')),
            ('Name', info.get('name', '')),
            ('Description', info.get('description', '')),
            ('Skill Evaluation', info.get('skillEvaluationMethod', '')),
            ('Calling Party Name', info.get('callingPartyName', '')),
            ('Calling Party Number', info.get('callingPartyNumber', '')),
        ]:
            self.info_row(label, value or '\u2014')

        # ACW Settings
        acw = info.get('acwSettings', {})
        if acw:
            ui.label('After Call Work').classes('text-h6 q-mt-md')
            self.info_row('Wrapup Prompt', acw.get('wrapupPrompt', '\u2014'))
            timeout = acw.get('timeoutMs')
            self.info_row('Timeout', f"{timeout // 1000} seconds" if timeout else '\u2014')

        # Media Settings
        media = info.get('mediaSettings', {})
        if media:
            ui.label('Media Settings').classes('text-h6 q-mt-md')
            for media_type, settings in media.items():
                if isinstance(settings, dict):
                    alert = settings.get('alertingTimeoutSeconds')
                    if alert:
                        self.info_row(f'{media_type.title()} Alert', f'{alert} seconds')

        # Queue Flow
        qf = info.get('queueFlow')
        if qf:
            ui.label('Queue Flow').classes('text-h6 q-mt-md')
            self.info_row('Flow', qf.get('name', qf.get('id', '\u2014')))

        # Raw JSON
        with ui.expansion('Raw JSON').classes('q-mt-md'):
            ui.code(json.dumps(info, indent=2, default=str)).classes('w-full')

    def _page_export(self) -> None:
        info = self.get_state('queue_info')
        if not info:
            self.navigate('list')
            return
        self._queue_header()
        self.section_title('Export')

        members = self.get_state('members', [])
        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'email', 'label': 'Email', 'field': 'email', 'sortable': True, 'align': 'left'},
            {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
        ]
        rows = [{
            'id': m.get('id', m.get('user', {}).get('id', '')),
            'name': m.get('name', m.get('user', {}).get('name', '')),
            'email': m.get('email', m.get('user', {}).get('email', '')),
        } for m in members]

        name = info.get('name', 'queue')

        csv_lines = ['Name,Email,ID']
        for r in rows:
            csv_lines.append(f"{r['name']},{r['email']},{r['id']}")
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
