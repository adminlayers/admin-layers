"""
User Manager Form: View users and bulk edit profiles
"""
from anvil import *
import anvil.server


class UserManagerForm(ColumnPanel):
    def __init__(self, demo_mode=False, **properties):
        super().__init__(**properties)
        self.demo_mode = demo_mode
        self.spacing = "medium"

        # Title
        self.add_component(Label(text="User Manager", role="headline"))
        self.add_component(Spacer(height=10))

        # Tab navigation
        tabs = FlowPanel(spacing="small")
        self.list_tab_btn = Button(text="All Users", icon="fa:list", role="primary")
        self.list_tab_btn.set_event_handler('click', lambda **e: self.show_tab('list'))
        tabs.add_component(self.list_tab_btn)

        self.bulk_edit_tab_btn = Button(text="Bulk Edit", icon="fa:edit", role="outlined")
        self.bulk_edit_tab_btn.set_event_handler('click', lambda **e: self.show_tab('bulk_edit'))
        tabs.add_component(self.bulk_edit_tab_btn)

        self.add_component(tabs)
        self.add_component(Spacer(height=20))

        # Content area
        self.content_panel = ColumnPanel()
        self.add_component(self.content_panel)

        # Show list by default
        self.current_tab = 'list'
        self.show_tab('list')

    def show_tab(self, tab_name):
        """Switch between tabs"""
        self.current_tab = tab_name
        self.content_panel.clear()

        # Update button styles
        if tab_name == 'list':
            self.list_tab_btn.role = "primary"
            self.bulk_edit_tab_btn.role = "outlined"
            self.show_list_tab()
        elif tab_name == 'bulk_edit':
            self.list_tab_btn.role = "outlined"
            self.bulk_edit_tab_btn.role = "primary"
            self.show_bulk_edit_tab()

    def show_list_tab(self):
        """Show list of users"""
        card = ColumnPanel(role="card")
        card.add_component(Label(text="All Users", bold=True, font_size=16))
        card.add_component(Spacer(height=10))

        # Load button
        load_btn = Button(text="Load Users", icon="fa:refresh", role="primary")
        load_btn.set_event_handler('click', self.load_users)
        card.add_component(load_btn)
        card.add_component(Spacer(height=10))

        # Data grid for users
        self.users_grid = DataGrid(
            columns=[
                {"id": "name", "title": "Name", "data_key": "name"},
                {"id": "email", "title": "Email", "data_key": "email"},
                {"id": "department", "title": "Department", "data_key": "department"},
                {"id": "title", "title": "Title", "data_key": "title"},
                {"id": "state", "title": "State", "data_key": "state"},
            ],
            rows_per_page=25
        )
        card.add_component(self.users_grid)

        self.content_panel.add_component(card)

    def load_users(self, **event_args):
        """Load users from API"""
        try:
            if self.demo_mode:
                result = anvil.server.call('demo_users_list_page', 25, 1)
            else:
                result = anvil.server.call('users_list_page', 25, 1)

            if result['success']:
                self.users_grid.items = result['data']['entities']
                alert(f"Loaded {len(result['data']['entities'])} users", title="Success")
            else:
                alert(f"Error: {result.get('error', 'Unknown error')}", title="Error")
        except Exception as e:
            alert(f"Failed to load users: {str(e)}", title="Error")

    def show_bulk_edit_tab(self):
        """Show bulk edit form"""
        card = ColumnPanel(role="card")
        card.add_component(Label(text="Bulk Edit Profiles", bold=True, font_size=16))
        card.add_component(Spacer(height=10))

        # Instructions
        info_text = """Upload or paste CSV data to update multiple user profiles at once.

CSV Format:
- Required column: email (to identify users)
- Optional columns: name, department, title, state

Example CSV:
email,title,department
alice@company.com,Senior Agent,Support
bob@company.com,Team Lead,Support"""

        card.add_component(Label(text=info_text, foreground="theme:On Surface Variant"))
        card.add_component(Spacer(height=20))

        # CSV input
        card.add_component(Label(text="Paste CSV Data:", bold=True))
        self.csv_input = TextArea(placeholder="email,title,department\nalice@company.com,Senior Agent,Support",
                                   rows=10)
        card.add_component(self.csv_input)
        card.add_component(Spacer(height=10))

        # Dry run checkbox
        self.dry_run_checkbox = CheckBox(text="Preview only (dry run)", checked=True)
        card.add_component(self.dry_run_checkbox)
        card.add_component(Spacer(height=10))

        # Process button
        process_btn = Button(text="Process CSV", icon="fa:play", role="primary")
        process_btn.set_event_handler('click', self.process_bulk_edit)
        card.add_component(process_btn)
        card.add_component(Spacer(height=20))

        # Results area
        self.results_panel = ColumnPanel()
        card.add_component(self.results_panel)

        self.content_panel.add_component(card)

    def process_bulk_edit(self, **event_args):
        """Process bulk edit CSV"""
        csv_text = self.csv_input.text
        if not csv_text or not csv_text.strip():
            alert("Please enter CSV data", title="Error")
            return

        dry_run = self.dry_run_checkbox.checked
        self.results_panel.clear()

        # Show progress
        self.results_panel.add_component(Label(text="Processing...", bold=True))

        try:
            # Parse CSV
            lines = csv_text.strip().split('\n')
            if len(lines) < 2:
                alert("CSV must have at least a header row and one data row", title="Error")
                return

            # Parse header
            header = [col.strip() for col in lines[0].split(',')]
            if 'email' not in header:
                alert("CSV must have an 'email' column", title="Error")
                return

            # Supported fields
            update_fields = {'name', 'department', 'title', 'state'}
            fields_to_update = set(header) & update_fields

            if not fields_to_update:
                alert(f"CSV must have at least one update field: {', '.join(update_fields)}", title="Error")
                return

            # Parse rows and prepare updates
            found_users = []
            missing_emails = []
            updates_to_apply = []

            for i, line in enumerate(lines[1:]):
                if not line.strip():
                    continue

                values = [v.strip() for v in line.split(',')]
                row = dict(zip(header, values))
                email = row.get('email', '').strip()

                if not email:
                    continue

                # Look up user by email
                if self.demo_mode:
                    user_result = anvil.server.call('demo_users_search_by_email', email)
                else:
                    user_result = anvil.server.call('users_search_by_email', email)

                if user_result['success']:
                    user = user_result['data']
                    payload = {}
                    for field in fields_to_update:
                        value = row.get(field, '').strip()
                        if value:
                            payload[field] = value

                    if payload:
                        found_users.append({
                            'email': email,
                            'name': user.get('name', ''),
                            'updates': payload
                        })
                        updates_to_apply.append({
                            'user_id': user['id'],
                            'payload': payload
                        })
                else:
                    missing_emails.append(email)

            # Display results
            self.results_panel.clear()
            self.results_panel.add_component(Label(text="Results:", bold=True, font_size=16))
            self.results_panel.add_component(Spacer(height=10))

            # Success card
            if found_users:
                success_card = ColumnPanel(role="card")
                success_card.add_component(Label(text=f"✓ {len(found_users)} users found",
                                                  foreground="theme:Success", bold=True))
                success_card.add_component(Spacer(height=10))

                # Show preview
                for u in found_users[:10]:  # Show first 10
                    updates_str = ", ".join([f"{k}={v}" for k, v in u['updates'].items()])
                    success_card.add_component(Label(text=f"{u['email']}: {updates_str}"))

                if len(found_users) > 10:
                    success_card.add_component(Label(text=f"... and {len(found_users) - 10} more"))

                self.results_panel.add_component(success_card)
                self.results_panel.add_component(Spacer(height=10))

            # Error card
            if missing_emails:
                error_card = ColumnPanel(role="card")
                error_card.add_component(Label(text=f"✗ {len(missing_emails)} not found",
                                                foreground="theme:Error", bold=True))
                error_card.add_component(Spacer(height=10))
                for email in missing_emails[:10]:  # Show first 10
                    error_card.add_component(Label(text=f"- {email}"))
                if len(missing_emails) > 10:
                    error_card.add_component(Label(text=f"... and {len(missing_emails) - 10} more"))
                self.results_panel.add_component(error_card)
                self.results_panel.add_component(Spacer(height=10))

            if not found_users:
                alert("No users found to update", title="Info")
                return

            # Dry run or execute
            if dry_run:
                info_card = ColumnPanel(role="card")
                info_card.add_component(Label(text="✓ Dry run complete", foreground="theme:Primary", bold=True))
                info_card.add_component(Label(text=f"{len(found_users)} users would be updated"))
                info_card.add_component(Label(text="Uncheck 'Preview only' to apply changes"))
                self.results_panel.add_component(info_card)
            else:
                # Execute bulk update
                self.results_panel.add_component(Label(text="Applying updates...", bold=True))

                if self.demo_mode:
                    result = anvil.server.call('demo_users_bulk_update', updates_to_apply)
                else:
                    result = anvil.server.call('users_bulk_update', updates_to_apply)

                if result['success']:
                    final_card = ColumnPanel(role="card")
                    final_card.add_component(Label(text="Complete!", bold=True, font_size=16))
                    final_card.add_component(Spacer(height=10))
                    final_card.add_component(Label(text=f"✓ Successful: {result['success_count']}",
                                                    foreground="theme:Success"))
                    if result['error_count'] > 0:
                        final_card.add_component(Label(text=f"✗ Failed: {result['error_count']}",
                                                        foreground="theme:Error"))
                    self.results_panel.add_component(final_card)
                    alert(f"Successfully updated {result['success_count']} user profile(s)!", title="Success")
                else:
                    alert(f"Error: {result.get('error', 'Unknown error')}", title="Error")

        except Exception as e:
            self.results_panel.clear()
            self.results_panel.add_component(Label(text=f"Error: {str(e)}", foreground="theme:Error"))
            alert(f"Failed to process CSV: {str(e)}", title="Error")
