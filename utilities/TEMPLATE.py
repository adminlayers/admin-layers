"""
[Utility Name]
[Brief description of what this utility does.]

Copy this template to create new utilities:
1. Copy this file and rename it (e.g., queue_manager.py)
2. Replace all [placeholders] with your values
3. Update utilities/__init__.py to export your class
4. Register in app.py UTILITY_CLASSES list
"""

from typing import List, Dict, Optional, Any

from nicegui import ui

from .base import BaseUtility, UtilityConfig


class TemplateUtility(BaseUtility):
    """
    [Utility Name]

    Features:
    - [Feature 1]
    - [Feature 2]
    - [Feature 3]

    Usage:
        # This utility is loaded automatically when registered in app.py
        # Users select it from the sidebar navigation
    """

    # =========================================================================
    # Configuration
    # =========================================================================

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="template_utility",
            name="Template Utility",
            description="Template for new utilities",
            icon="build",
            category="General",
            requires_group=False,
            requires_queue=False,
            requires_user=False,
            tags=["template", "example"],
        )

    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    def init_state(self) -> None:
        if self.get_state('initialized') is None:
            self.set_state('initialized', True)
            self.set_state('page', 'main')
            self.set_state('data', [])
            self.set_state('selected', None)

    def cleanup(self) -> None:
        pass

    # =========================================================================
    # Sidebar Rendering
    # =========================================================================

    def render_sidebar(self) -> None:
        self.nav_button('Main View', 'main', icon='home')
        self.nav_button('Action View', 'action', icon='play_arrow')
        self.nav_button('Export', 'export', icon='download')

    # =========================================================================
    # Main Content Rendering
    # =========================================================================

    def render_main(self) -> None:
        self.init_state()
        page = self.get_state('page', 'main')
        {
            'main': self._render_main_page,
            'action': self._render_action_page,
            'export': self._render_export_page,
        }.get(page, self._render_main_page)()

    def _render_main_page(self) -> None:
        config = self.get_config()
        data = self.get_state('data', [])

        self.section_title(config.name)

        if not data:
            ui.label('No data loaded. Use controls above to get started.').classes(
                'text-grey-6')
            return

        ui.label(f'{len(data)} items loaded').classes('text-caption text-grey-6')

        columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'status', 'label': 'Status', 'field': 'status', 'sortable': True},
        ]
        rows = [{'id': item.get('id', ''), 'name': item.get('name', ''),
                 'status': item.get('status', '')} for item in data]

        self.make_table(
            columns, rows,
            on_row_click=lambda row: ui.notify(f"Clicked: {row.get('name')}"),
            title='Click a row to select',
        )

    def _render_action_page(self) -> None:
        self.back_button('Back to Main')
        self.section_title('Actions')

        emails_input = ui.textarea(
            'Enter items (one per line)',
            placeholder='item1\nitem2\nitem3',
        ).classes('w-full').style('min-height:150px')

        dry_run = ui.checkbox('Preview only (dry run)', value=True)

        def do_process():
            items = [l.strip() for l in (emails_input.value or '').split('\n') if l.strip()]
            if not items:
                ui.notify('No valid items found', type='warning')
                return
            if dry_run.value:
                ui.notify(f'Dry run: {len(items)} items would be processed', type='info')
            else:
                ui.notify(f'Processed {len(items)} items', type='positive')

        ui.button('Process', icon='play_arrow', on_click=do_process).props(
            'color=primary no-caps').classes('q-mt-sm')

    def _render_export_page(self) -> None:
        self.back_button('Back to Main')
        self.section_title('Export')

        data = self.get_state('data', [])
        ui.label(f'{len(data)} items available for export').classes(
            'text-caption text-grey-6')

        # Build export data
        csv_lines = ['Name,Status,ID']
        for item in data:
            csv_lines.append(f"{item.get('name','')},{item.get('status','')},{item.get('id','')}")
        csv_data = '\n'.join(csv_lines)

        with ui.row().classes('q-gutter-sm'):
            ui.button('Download CSV', icon='download',
                      on_click=lambda: ui.download(csv_data.encode(), 'export.csv')).props('no-caps')
