"""
Main Form: Navigation and Layout
"""
from ._anvil_designer import MainFormTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
from anvil.tables import app_tables


class MainForm(MainFormTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)

        self.connected = False
        self.demo_mode = False
        self.current_utility = None

        # Show login form initially
        self.show_login()

    def show_login(self):
        """Show login form"""
        from .LoginForm import LoginForm
        self.content_panel.clear()
        login_form = LoginForm(on_connected=self.on_connected)
        self.content_panel.add_component(login_form)
        self.nav_panel.visible = False

    def on_connected(self, demo=False):
        """Called when successfully connected"""
        self.connected = True
        self.demo_mode = demo
        self.show_home()
        self.setup_navigation()
        self.nav_panel.visible = True

    def setup_navigation(self):
        """Setup navigation buttons"""
        self.nav_home_btn.set_event_handler('click', self.show_home)
        self.nav_users_btn.set_event_handler('click', lambda **e: self.show_utility('users'))
        self.nav_groups_btn.set_event_handler('click', lambda **e: self.show_utility('groups'))
        self.nav_queues_btn.set_event_handler('click', lambda **e: self.show_utility('queues'))
        self.nav_skills_btn.set_event_handler('click', lambda **e: self.show_utility('skills'))
        self.disconnect_btn.set_event_handler('click', self.disconnect)

        if self.demo_mode:
            self.connection_label.text = "Demo Mode"
            self.connection_label.foreground = "#fbbf24"
        else:
            self.connection_label.text = "Connected"
            self.connection_label.foreground = "#4ade80"

    def show_home(self, **event_args):
        """Show home screen"""
        self.content_panel.clear()
        self.current_utility = None

        card = ColumnPanel()
        card.add_component(Label(text="Admin Layers", role="headline"))
        card.add_component(Spacer(height=20))

        if self.demo_mode:
            demo_label = Label(text="⚡ Demo Mode - Sample data only", foreground="#fbbf24")
            card.add_component(demo_label)
            card.add_component(Spacer(height=20))

        card.add_component(Label(text="Select a utility from the sidebar to begin", role="subheading"))
        card.add_component(Spacer(height=40))

        # Utility cards
        utilities = [
            ("User Manager", "Manage users and bulk edit profiles", "users"),
            ("Group Manager", "View and manage group membership", "groups"),
            ("Queue Manager", "Manage queue membership", "queues"),
            ("Skill Manager", "Assign and manage routing skills", "skills"),
        ]

        for name, desc, util_id in utilities:
            util_card = ColumnPanel(spacing=10)
            util_card.role = "card"
            util_card.add_component(Label(text=name, bold=True, font_size=18))
            util_card.add_component(Label(text=desc, foreground="#94a3b8"))

            btn = Button(text="Open", icon="fa:arrow-right")
            btn.set_event_handler('click', lambda **e, uid=util_id: self.show_utility(uid))
            util_card.add_component(btn)

            card.add_component(util_card)
            card.add_component(Spacer(height=10))

        self.content_panel.add_component(card)

    def show_utility(self, utility_id):
        """Show a utility form"""
        self.current_utility = utility_id
        self.content_panel.clear()

        if utility_id == 'users':
            from .UserManagerForm import UserManagerForm
            form = UserManagerForm(demo_mode=self.demo_mode)
        elif utility_id == 'groups':
            from .GroupManagerForm import GroupManagerForm
            form = GroupManagerForm(demo_mode=self.demo_mode)
        elif utility_id == 'queues':
            from .QueueManagerForm import QueueManagerForm
            form = QueueManagerForm(demo_mode=self.demo_mode)
        elif utility_id == 'skills':
            from .SkillManagerForm import SkillManagerForm
            form = SkillManagerForm(demo_mode=self.demo_mode)
        else:
            form = Label(text=f"Utility '{utility_id}' not implemented yet")

        self.content_panel.add_component(form)

    def disconnect(self, **event_args):
        """Disconnect and return to login"""
        anvil.server.call('disconnect_genesys')
        self.connected = False
        self.demo_mode = False
        self.show_login()
