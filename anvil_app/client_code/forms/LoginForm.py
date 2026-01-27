"""
Login Form: Authentication
"""
from anvil import *
import anvil.server


class LoginForm(ColumnPanel):
    def __init__(self, on_connected=None, **properties):
        super().__init__(**properties)
        self.on_connected = on_connected
        self.spacing = "medium"

        # Title
        self.add_component(Label(text="Admin Layers", role="headline", align="center"))
        self.add_component(Label(text="Genesys Cloud Administration Tool", role="subheading", align="center"))
        self.add_component(Spacer(height=40))

        # Card for login
        card = ColumnPanel(role="card")
        card.add_component(Label(text="Connect to Genesys Cloud", bold=True, font_size=18))
        card.add_component(Spacer(height=20))

        # Client ID
        self.client_id_input = TextBox(placeholder="OAuth Client ID")
        card.add_component(Label(text="Client ID"))
        card.add_component(self.client_id_input)
        card.add_component(Spacer(height=10))

        # Client Secret
        self.client_secret_input = TextBox(placeholder="OAuth Client Secret", hide_text=True)
        card.add_component(Label(text="Client Secret"))
        card.add_component(self.client_secret_input)
        card.add_component(Spacer(height=10))

        # Region
        self.region_dropdown = DropDown(
            items=["mypurecloud.com", "mypurecloud.ie", "mypurecloud.de",
                   "mypurecloud.com.au", "mypurecloud.jp", "usw2.pure.cloud",
                   "cac1.pure.cloud", "euw2.pure.cloud", "apne2.pure.cloud"],
            selected_value="mypurecloud.com"
        )
        card.add_component(Label(text="Region"))
        card.add_component(self.region_dropdown)
        card.add_component(Spacer(height=20))

        # Buttons
        btn_panel = FlowPanel(spacing="medium")
        connect_btn = Button(text="Connect", icon="fa:link", role="primary")
        connect_btn.set_event_handler('click', self.connect_click)
        btn_panel.add_component(connect_btn)

        demo_btn = Button(text="Demo Mode", icon="fa:play", role="outlined")
        demo_btn.set_event_handler('click', self.demo_click)
        btn_panel.add_component(demo_btn)

        card.add_component(btn_panel)

        self.add_component(card)

        # Status label
        self.status_label = Label(text="", foreground="theme:Error")
        self.add_component(self.status_label)

    def connect_click(self, **event_args):
        """Connect to Genesys Cloud"""
        client_id = self.client_id_input.text
        client_secret = self.client_secret_input.text
        region = self.region_dropdown.selected_value

        if not client_id or not client_secret:
            self.status_label.text = "Please enter Client ID and Client Secret"
            return

        self.status_label.text = "Connecting..."
        self.status_label.foreground = "theme:Primary"

        try:
            result = anvil.server.call('connect_genesys', client_id, client_secret, region)

            if result['success']:
                anvil.server.call('set_demo_mode', False)
                self.status_label.text = "Connected successfully!"
                self.status_label.foreground = "theme:Success"
                if self.on_connected:
                    self.on_connected(demo=False)
            else:
                self.status_label.text = f"Error: {result.get('error', 'Unknown error')}"
                self.status_label.foreground = "theme:Error"
        except Exception as e:
            self.status_label.text = f"Connection failed: {str(e)}"
            self.status_label.foreground = "theme:Error"

    def demo_click(self, **event_args):
        """Enter demo mode"""
        anvil.server.call('set_demo_mode', True)
        if self.on_connected:
            self.on_connected(demo=True)
