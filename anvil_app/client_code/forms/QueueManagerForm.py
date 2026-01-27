"""
Queue Manager Form: View and manage queues
"""
from anvil import *
import anvil.server


class QueueManagerForm(ColumnPanel):
    def __init__(self, demo_mode=False, **properties):
        super().__init__(**properties)
        self.demo_mode = demo_mode
        self.spacing = "medium"

        # Title
        self.add_component(Label(text="Queue Manager", role="headline"))
        self.add_component(Spacer(height=20))

        # Card
        card = ColumnPanel(role="card")
        card.add_component(Label(text="All Queues", bold=True, font_size=16))
        card.add_component(Spacer(height=10))

        # Load button
        load_btn = Button(text="Load Queues", icon="fa:refresh", role="primary")
        load_btn.set_event_handler('click', self.load_queues)
        card.add_component(load_btn)
        card.add_component(Spacer(height=10))

        # Data grid
        self.queues_grid = DataGrid(
            columns=[
                {"id": "name", "title": "Name", "data_key": "name"},
                {"id": "memberCount", "title": "Members", "data_key": "memberCount"},
            ],
            rows_per_page=25
        )
        card.add_component(self.queues_grid)

        self.add_component(card)

    def load_queues(self, **event_args):
        """Load queues from API"""
        try:
            if self.demo_mode:
                result = anvil.server.call('demo_queues_list_page', 25, 1)
            else:
                result = anvil.server.call('queues_list_page', 25, 1)

            if result['success']:
                self.queues_grid.items = result['data']['entities']
                alert(f"Loaded {len(result['data']['entities'])} queues", title="Success")
            else:
                alert(f"Error: {result.get('error', 'Unknown error')}", title="Error")
        except Exception as e:
            alert(f"Failed to load queues: {str(e)}", title="Error")
