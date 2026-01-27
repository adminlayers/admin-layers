"""
Admin Layers - Genesys Cloud Administration Tool
Built with NiceGUI (Quasar/Vue.js) for native mobile support.
"""

import os
from typing import Any, Dict, Optional

from nicegui import app, ui

from core.demo import DemoAPI, is_demo_mode, set_demo_mode
from core.encrypted_storage import get_storage
from utilities import (
    GroupManagerUtility,
    QueueManagerUtility,
    SkillManagerUtility,
    UserManagerUtility,
)

# =============================================================================
# Utility registry
# =============================================================================

UTILITY_CLASSES = [
    GroupManagerUtility,
    QueueManagerUtility,
    SkillManagerUtility,
    UserManagerUtility,
]


# =============================================================================
# State helpers (use app.storage.user per-session dict)
# =============================================================================

def _ss() -> Dict:
    return app.storage.user


def _get(key: str, default: Any = None) -> Any:
    return _ss().get(key, default)


def _set(key: str, value: Any) -> None:
    _ss()[key] = value


# =============================================================================
# API helpers
# =============================================================================

def get_api():
    if is_demo_mode():
        return DemoAPI()
    # Try stored credentials
    storage = get_storage()
    creds = storage.retrieve_credentials()
    if creds:
        try:
            from genesys_cloud.api import GenesysCloudAPI
            return GenesysCloudAPI(
                client_id=creds['client_id'],
                client_secret=creds['client_secret'],
                region=creds['region'],
            )
        except Exception:
            pass
    return None


# =============================================================================
# Main page
# =============================================================================

@ui.page('/')
def main_page():
    ui.dark_mode(True)
    ui.colors(primary='#3b82f6')

    ui.add_head_html('''
    <style>
        .q-drawer { background-color: #1a2632 !important; }
        .q-header { background-color: #0f172a !important; }
        body { background-color: #0f172a; color: #e2e8f0; }
        .q-table--dark .q-table__top,
        .q-table--dark .q-table__bottom { color: #cbd5e1; }
        .q-table--dark tbody tr:hover { background: rgba(59,130,246,0.08) !important; }
        .nav-section-label {
            font-size: 0.7rem; font-weight: 600; color: #64748b;
            text-transform: uppercase; letter-spacing: 0.05em;
            padding: 12px 16px 4px;
        }
    </style>
    ''')

    state = _ss()
    content_area = None
    sidebar_area = None
    drawer = None

    def get_current_utility():
        uid = _get('active_utility')
        if not uid or uid.startswith('_'):
            return None
        api = get_api()
        if not api:
            return None
        for cls in UTILITY_CLASSES:
            cfg = cls.get_config()
            if cfg.id == uid:
                return cls(api, state, refresh_content)
        return None

    def refresh_content():
        nonlocal content_area, sidebar_area
        if content_area:
            content_area.clear()
            with content_area:
                render_main_content()
        if sidebar_area:
            sidebar_area.clear()
            with sidebar_area:
                render_sidebar_content()

    def switch_utility(utility_id: str):
        _set('active_utility', utility_id)
        refresh_content()

    def go_home():
        _set('active_utility', '')
        refresh_content()

    def activate_demo():
        set_demo_mode(True)
        _set('connected', True)
        _set('active_utility', '')
        refresh_content()

    def connect_real(client_id, client_secret, region):
        try:
            from genesys_cloud.api import GenesysCloudAPI
            GenesysCloudAPI(
                client_id=client_id, client_secret=client_secret, region=region,
            )
            _set('connected', True)
            storage = get_storage()
            storage.store_credentials(client_id, client_secret, region)
            ui.notify('Connected to Genesys Cloud', type='positive')
            refresh_content()
        except Exception as exc:
            ui.notify(f'Connection failed: {exc}', type='negative')

    def disconnect():
        _set('connected', False)
        _set('active_utility', '')
        set_demo_mode(False)
        storage = get_storage()
        storage.clear_credentials()
        refresh_content()

    # -- Render helpers --

    def render_sidebar_content():
        connected = _get('connected', False)

        ui.label('Admin Layers').classes('text-h6 text-white q-pa-md')

        if not connected:
            ui.label('Not connected').classes('text-caption text-grey-6 q-px-md')
            return

        if is_demo_mode():
            with ui.element('div').classes('q-px-md q-pb-sm'):
                ui.badge('DEMO MODE', color='amber').props('outline')

        ui.button('Home', icon='home', on_click=go_home).props(
            'flat dense align=left no-caps').classes('w-full')
        ui.separator().classes('q-my-xs')

        active_id = _get('active_utility', '')

        categories: Dict[str, list] = {}
        for cls in UTILITY_CLASSES:
            cfg = cls.get_config()
            categories.setdefault(cfg.category, []).append(cfg)

        for cat, configs in categories.items():
            ui.label(cat).classes('nav-section-label')
            for cfg in configs:
                is_active = cfg.id == active_id
                color = 'primary' if is_active else None
                flat = not is_active
                ui.button(
                    cfg.name, icon=_icon_for(cfg.id),
                    on_click=lambda cid=cfg.id: switch_utility(cid),
                    color=color,
                ).props(f'{"flat " if flat else ""}dense align=left no-caps').classes('w-full')

        utility = get_current_utility()
        if utility:
            ui.separator().classes('q-my-xs')
            ui.label(utility.get_config().name).classes('nav-section-label')
            utility.render_sidebar()

        ui.space()
        ui.separator().classes('q-my-xs')
        ui.button('Storage Info', icon='info', on_click=lambda: (
            _set('active_utility', '_storage'), refresh_content()
        )).props('flat dense align=left no-caps').classes('w-full')
        ui.button('Disconnect', icon='logout', on_click=disconnect).props(
            'flat dense align=left no-caps color=red').classes('w-full')

    def render_main_content():
        connected = _get('connected', False)
        if not connected:
            render_connect_page()
            return
        active = _get('active_utility', '')
        if active == '_storage':
            render_storage_info()
        elif active:
            utility = get_current_utility()
            if utility:
                utility.init_state()
                utility.render_main()
            else:
                render_home()
        else:
            render_home()

    def render_connect_page():
        with ui.column().classes('w-full items-center q-pa-xl'):
            ui.label('Admin Layers').classes('text-h3 text-weight-bold')
            ui.label('Genesys Cloud Administration Tool').classes(
                'text-subtitle1 text-grey-6 q-mb-lg')
            with ui.card().classes('w-full').style('max-width:480px'):
                ui.label('Connect to Genesys Cloud').classes('text-h6 q-mb-md')
                client_id = ui.input('Client ID', placeholder='OAuth Client ID').classes('w-full')
                client_secret = ui.input('Client Secret', placeholder='OAuth Client Secret',
                                         password=True, password_toggle_button=True).classes('w-full')
                region = ui.select(
                    ['mypurecloud.com', 'mypurecloud.ie', 'mypurecloud.de',
                     'mypurecloud.com.au', 'mypurecloud.jp', 'usw2.pure.cloud',
                     'cac1.pure.cloud', 'euw2.pure.cloud', 'apne2.pure.cloud',
                     'aps1.pure.cloud', 'sae1.pure.cloud', 'mec1.pure.cloud'],
                    value='mypurecloud.com', label='Region',
                ).classes('w-full')
                with ui.row().classes('w-full q-gutter-sm q-mt-md'):
                    ui.button('Connect', icon='link',
                              on_click=lambda: connect_real(
                                  client_id.value, client_secret.value, region.value),
                              ).props('color=primary')
                    ui.button('Demo Mode', icon='play_arrow',
                              on_click=activate_demo,
                              ).props('outline color=amber')
                storage = get_storage()
                creds = storage.retrieve_credentials()
                if creds:
                    ui.separator().classes('q-my-md')
                    ui.label('Saved credentials found').classes('text-caption text-grey-6')
                    ui.button('Reconnect', icon='refresh',
                              on_click=lambda: connect_real(
                                  creds['client_id'], creds['client_secret'], creds['region']),
                              ).props('flat color=primary')

    def render_home():
        with ui.column().classes('w-full q-pa-md'):
            ui.label('Admin Layers').classes('text-h4 text-weight-bold')
            if is_demo_mode():
                ui.badge('DEMO MODE', color='amber').props('outline')
            ui.label('Select a utility from the sidebar to get started.').classes(
                'text-subtitle1 text-grey-6 q-mb-lg')
            with ui.row().classes('w-full q-gutter-md'):
                for cls in UTILITY_CLASSES:
                    cfg = cls.get_config()
                    with ui.card().on('click', lambda cid=cfg.id: switch_utility(cid)).classes(
                            'cursor-pointer col-12 col-sm-5 col-md-3'):
                        with ui.card_section():
                            with ui.row().classes('items-center q-gutter-sm'):
                                ui.icon(_icon_for(cfg.id), size='sm', color='primary')
                                ui.label(cfg.name).classes('text-h6')
                            ui.label(cfg.description).classes('text-caption text-grey-6')

    def render_storage_info():
        with ui.column().classes('w-full q-pa-md'):
            ui.button('Back', icon='arrow_back', on_click=go_home).props('flat dense no-caps')
            ui.label('Storage Info').classes('text-h5 q-mb-md')
            storage = get_storage()
            info = storage.get_storage_info()
            with ui.card().classes('w-full').style('max-width:480px'):
                for key, val in info.items():
                    with ui.row().classes('q-gutter-sm items-center'):
                        ui.label(key.replace('_', ' ').title()).classes(
                            'text-caption text-grey-6 text-uppercase')
                        ui.label(str(val)).classes('text-body2')

    # -- Layout --

    with ui.header().classes('items-center q-px-md'):
        ui.button(icon='menu', on_click=lambda: drawer.toggle()).props(
            'flat round color=white dense')
        ui.label('Admin Layers').classes('text-h6 text-white q-ml-sm')

    with ui.left_drawer(value=True, bordered=True).classes('column') as drawer:
        sidebar_area = ui.column().classes('w-full column flex-grow')
        with sidebar_area:
            render_sidebar_content()

    with ui.column().classes('w-full q-pa-none'):
        content_area = ui.column().classes('w-full')
        with content_area:
            render_main_content()


def _icon_for(utility_id: str) -> str:
    return {
        'group_manager': 'group',
        'queue_manager': 'phone_in_talk',
        'skill_manager': 'psychology',
        'user_manager': 'person',
    }.get(utility_id, 'build')


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title='Admin Layers',
        dark=True,
        storage_secret='admin-layers-secret',
        port=int(os.environ.get('PORT', 8080)),
        reload=os.environ.get('DEV', '') == '1',
    )
