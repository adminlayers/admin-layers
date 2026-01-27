"""
Group Manager Form: View and manage groups
"""
from anvil import *
import anvil.server


class GroupManagerForm(ColumnPanel):
    def __init__(self, demo_mode=False, **properties):
        super().__init__(**properties)
        self.demo_mode = demo_mode
        self.spacing = "medium"

        # Title
        self.add_component(Label(text="Group Manager", role="headline"))
        self.add_component(Spacer(height=20))

        # Card
        card = ColumnPanel(role="card")
        card.add_component(Label(text="All Groups", bold=True, font_size=16))
        card.add_component(Spacer(height=10))

        # Load button
        load_btn = Button(text="Load Groups", icon="fa:refresh", role="primary")
        load_btn.set_event_handler('click', self.load_groups)
        card.add_component(load_btn)
        card.add_component(Spacer(height=10))

        # Data grid
        self.groups_grid = DataGrid(
            columns=[
                {"id": "name", "title": "Name", "data_key": "name"},
                {"id": "type", "title": "Type", "data_key": "type"},
                {"id": "visibility", "title": "Visibility", "data_key": "visibility"},
                {"id": "memberCount", "title": "Members", "data_key": "memberCount"},
            ],
            rows_per_page=25
        )
        card.add_component(self.groups_grid)

        self.add_component(card)

    def load_groups(self, **event_args):
        """Load groups from API"""
        try:
            if self.demo_mode:
                result = anvil.server.call('demo_groups_list_page', 25, 1)
            else:
                result = anvil.server.call('groups_list_page', 25, 1)

            if result['success']:
                self.groups_grid.items = result['data']['entities']
                alert(f"Loaded {len(result['data']['entities'])} groups", title="Success")
            else:
                alert(f"Error: {result.get('error', 'Unknown error')}", title="Error")
        except Exception as e:
            alert(f"Failed to load groups: {str(e)}", title="Error")
