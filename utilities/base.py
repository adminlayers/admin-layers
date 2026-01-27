"""
Base Utility for NiceGUI-based Admin Layers.

Provides the base class and configuration for all utility modules.
Utilities render into a NiceGUI container using Quasar components
with native mobile support, clickable tables, and responsive layout.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from nicegui import ui


@dataclass
class UtilityConfig:
    """Configuration for a utility module."""
    id: str
    name: str
    description: str
    icon: str = ""
    category: str = "General"
    requires_group: bool = False
    requires_queue: bool = False
    requires_user: bool = False
    tags: List[str] = field(default_factory=list)


class BaseUtility(ABC):
    """
    Base class for NiceGUI-based utility modules.

    Each utility owns a content container and re-renders it on navigation.
    State is stored in a shared dict (app.storage.user).
    """

    def __init__(self, api: Any, state: Dict, refresh_fn: Callable):
        self.api = api
        self._state = state
        self._refresh = refresh_fn

    @staticmethod
    @abstractmethod
    def get_config() -> UtilityConfig:
        pass

    @abstractmethod
    def render_sidebar(self) -> None:
        """Build sidebar navigation buttons into the current NiceGUI context."""
        pass

    @abstractmethod
    def render_main(self) -> None:
        """Build main content into the current NiceGUI context."""
        pass

    def init_state(self) -> None:
        pass

    def cleanup(self) -> None:
        pass

    # -- state helpers --

    def get_state(self, key: str, default: Any = None) -> Any:
        cfg = self.get_config()
        return self._state.get(f"{cfg.id}_{key}", default)

    def set_state(self, key: str, value: Any) -> None:
        cfg = self.get_config()
        self._state[f"{cfg.id}_{key}"] = value

    def navigate(self, page: str) -> None:
        """Change the current page and trigger a re-render."""
        self.set_state('page', page)
        self._refresh()

    # -- reusable UI helpers --

    def nav_button(self, label: str, page: str, icon: Optional[str] = None) -> None:
        current = self.get_state('page', 'list')
        color = 'primary' if current == page else None
        flat = current != page
        ui.button(
            label, icon=icon,
            on_click=lambda p=page: self.navigate(p),
            color=color,
        ).props(f'{"flat " if flat else ""}dense align=left no-caps').classes('w-full')

    def back_button(self, label: str = 'Back to list', page: str = 'list') -> None:
        ui.button(label, icon='arrow_back',
                  on_click=lambda: self.navigate(page),
                  ).props('flat dense no-caps')

    def section_title(self, text: str, subtitle: str = '') -> None:
        ui.label(text).classes('text-h5 q-mb-sm')
        if subtitle:
            ui.label(subtitle).classes('text-caption text-grey-6')

    def info_row(self, label: str, value: str) -> None:
        with ui.row().classes('items-center q-gutter-sm'):
            ui.label(label).classes('text-caption text-grey-6 text-uppercase')
            ui.label(value or '\u2014').classes('text-body2')

    def make_table(self, columns: List[Dict], rows: List[Dict],
                   row_key: str = 'id', on_row_click: Optional[Callable] = None,
                   pagination: int = 25, title: str = '') -> ui.table:
        """Create a Quasar table with search, pagination, and optional row click."""
        table = ui.table(
            columns=columns, rows=rows, row_key=row_key,
            pagination={'rowsPerPage': pagination, 'sortBy': columns[0]['name'] if columns else None},
            title=title,
        ).classes('w-full')
        table.props('flat bordered dense wrap-cells')
        table.add_slot('top-right', '''
            <q-input borderless dense debounce="300" v-model="props.filter" placeholder="Search...">
                <template v-slot:append><q-icon name="search" /></template>
            </q-input>
        ''')
        table.props('filter=""')
        if on_row_click:
            table.on('rowClick', lambda e: on_row_click(e.args[1]))
            table.classes('cursor-pointer')
        return table
