"""
Skill Manager Form: View and manage routing skills
"""
from anvil import *
import anvil.server


class SkillManagerForm(ColumnPanel):
    def __init__(self, demo_mode=False, **properties):
        super().__init__(**properties)
        self.demo_mode = demo_mode
        self.spacing = "medium"

        # Title
        self.add_component(Label(text="Skill Manager", role="headline"))
        self.add_component(Spacer(height=20))

        # Card
        card = ColumnPanel(role="card")
        card.add_component(Label(text="All Skills", bold=True, font_size=16))
        card.add_component(Spacer(height=10))

        # Load button
        load_btn = Button(text="Load Skills", icon="fa:refresh", role="primary")
        load_btn.set_event_handler('click', self.load_skills)
        card.add_component(load_btn)
        card.add_component(Spacer(height=10))

        # Data grid
        self.skills_grid = DataGrid(
            columns=[
                {"id": "name", "title": "Skill", "data_key": "name"},
                {"id": "state", "title": "State", "data_key": "state"},
            ],
            rows_per_page=25
        )
        card.add_component(self.skills_grid)

        self.add_component(card)

    def load_skills(self, **event_args):
        """Load skills from API"""
        try:
            if self.demo_mode:
                result = anvil.server.call('demo_routing_get_skills')
            else:
                result = anvil.server.call('routing_get_skills')

            if result['success']:
                self.skills_grid.items = result['data']
                alert(f"Loaded {len(result['data'])} skills", title="Success")
            else:
                alert(f"Error: {result.get('error', 'Unknown error')}", title="Error")
        except Exception as e:
            alert(f"Failed to load skills: {str(e)}", title="Error")
