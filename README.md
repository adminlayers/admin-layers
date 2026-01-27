# Admin Layers - Anvil App

Complete Python web application for Genesys Cloud administration built with Anvil.

## 🎯 Features

### User Manager
- **List Users**: View all users with pagination
- **Bulk Edit Profiles**: Upload CSV to update multiple user profiles at once
  - Update name, department, title, and state
  - Preview changes before applying (dry run mode)
  - Detailed success/error reporting

### Group Manager
- **List Groups**: View all groups with member counts
- **Manage Membership**: Add/remove users from groups (coming soon)

### Queue Manager
- **List Queues**: View all routing queues
- **Manage Members**: Add/remove queue members (coming soon)

### Skill Manager
- **List Skills**: View all routing skills
- **Assign Skills**: Bulk skill assignment (coming soon)

### Demo Mode
- Test all features without connecting to Genesys Cloud
- Sample data included for all utilities
- Perfect for training and demonstrations

## 🚀 Deployment to Anvil

### Option 1: Create New Anvil App (Recommended)

1. **Sign up for Anvil** (if you haven't already)
   - Go to https://anvil.works
   - Click "Sign Up" and create a free account

2. **Create a New App**
   - Click "Create New App"
   - Choose "Start with Blank App"
   - Name it "Admin Layers"

3. **Upload Server Code**
   - In the left sidebar, click "Server Code" dropdown
   - Click the "+" button to add a new module
   - Name it "genesys_api"
   - Copy the contents of `server_code/genesys_api.py` into this module

   - Click "+" again to add another module
   - Name it "demo_mode"
   - Copy the contents of `server_code/demo_mode.py` into this module

4. **Create Client Forms**
   - Click "Forms" in the left sidebar
   - Delete the default Form1

   - Click "+" to add a new form
   - Name it "MainForm"
   - Switch to Code view (click "Code" at the top)
   - Copy the contents of `client_code/forms/MainForm.py`
   - Paste it into the code editor

   - Repeat for each form:
     - LoginForm
     - UserManagerForm
     - GroupManagerForm
     - QueueManagerForm
     - SkillManagerForm

5. **Set MainForm as Startup Form**
   - Click the gear icon (⚙️) in the top right
   - Select "App Settings"
   - Under "Startup Form", select "MainForm"
   - Click "Save"

6. **Test the App**
   - Click the "Run" button (▶️) at the top
   - You should see the login screen
   - Click "Demo Mode" to test with sample data

### Option 2: Clone from Anvil

If you have an Anvil app already set up, you can clone it:

```bash
# Install anvil-app-server
pip install anvil-app-server

# Clone the app
anvil-app-server --app YOUR_APP_ID --app-origin https://anvil.works
```

## 📋 CSV Format for Bulk Edit

The bulk edit feature requires a CSV file with specific columns:

### Required Column
- `email` - User's email address (used to identify the user)

### Optional Columns (at least one required)
- `name` - Full name
- `department` - Department name
- `title` - Job title
- `state` - User state (`active` or `inactive`)

### Example CSV Files

**Simple (title and department only):**
```csv
email,title,department
alice.johnson@company.com,Senior Agent,Support
bob.martinez@company.com,Team Lead,Support
carol.williams@company.com,Account Executive,Sales
```

**Complete (all fields):**
```csv
email,name,department,title,state
alice@company.com,Alice Johnson,Support,Senior Agent,active
bob@company.com,Bob Martinez,Support,Team Lead,active
carol@company.com,Carol Williams,Sales,Account Executive,active
```

### CSV Guidelines
- First row must be the header with column names
- Only include columns you want to update
- Empty cells will be skipped (won't update that field)
- Users not found by email will be reported but won't stop processing
- Use "Preview only" checkbox to test before applying changes

## 🔧 Configuration

### Genesys Cloud OAuth Credentials

To connect to your Genesys Cloud organization:

1. **Create OAuth Client**
   - Log in to Genesys Cloud
   - Go to Admin → Integrations → OAuth
   - Click "Add Client"
   - Select "Client Credentials" grant type
   - Select appropriate roles (User, Group, Queue, Routing permissions)
   - Save and copy the Client ID and Client Secret

2. **Connect in App**
   - Launch the Anvil app
   - Enter your Client ID and Client Secret
   - Select your region
   - Click "Connect"

### Supported Regions
- mypurecloud.com (US East)
- mypurecloud.ie (Ireland)
- mypurecloud.de (Germany)
- mypurecloud.com.au (Australia)
- mypurecloud.jp (Japan)
- usw2.pure.cloud (US West)
- cac1.pure.cloud (Canada)
- euw2.pure.cloud (Europe West)
- apne2.pure.cloud (Asia Pacific Northeast)

## 🎨 Customization

### Styling
Anvil uses Material Design by default. You can customize:
- Colors: App Settings → Theme
- Fonts: App Settings → Theme
- Layout: Edit forms directly in the designer

### Adding New Features

1. **Add Server Functions**
   - Edit `server_code/genesys_api.py`
   - Add new `@anvil.server.callable` functions
   - Call them from client code with `anvil.server.call('function_name', args)`

2. **Add New Forms**
   - Create new form in Anvil Forms designer
   - Add to MainForm navigation
   - Implement UI and logic

3. **Extend Demo Mode**
   - Edit `server_code/demo_mode.py`
   - Add sample data
   - Create corresponding demo functions

## 📱 Mobile Support

Anvil apps work great on mobile devices:
- Responsive design automatically adapts to screen size
- Works in any mobile browser
- Can be added to home screen as a PWA (Progressive Web App)

## 🔒 Security

### Best Practices
1. **Never hardcode credentials** - Users enter them at login
2. **Use HTTPS** - Anvil provides this automatically
3. **Limit OAuth scopes** - Only grant necessary permissions
4. **Regular audits** - Monitor bulk operations
5. **Test in demo mode first** - Verify changes before production

### Session Management
- Each user gets their own isolated session
- Credentials are never stored permanently
- Session ends when user disconnects or closes browser

## 🐛 Troubleshooting

### "Not connected" Error
- Make sure you've clicked "Connect" or "Demo Mode"
- Verify OAuth credentials are correct
- Check that your OAuth client has necessary permissions

### API Errors
- Verify OAuth client has appropriate roles
- Check Genesys Cloud service status
- Ensure API rate limits aren't exceeded

### CSV Upload Issues
- Check that CSV has required 'email' column
- Verify CSV is properly formatted (no special characters)
- Make sure emails match existing users

## 📚 Development

### Project Structure
```
anvil_app/
├── anvil.yaml                     # App configuration
├── server_code/
│   ├── genesys_api.py            # Genesys Cloud API wrapper
│   └── demo_mode.py              # Demo data and functions
└── client_code/
    └── forms/
        ├── MainForm.py           # Main layout and navigation
        ├── LoginForm.py          # Authentication
        ├── UserManagerForm.py    # User management + bulk edit
        ├── GroupManagerForm.py   # Group management
        ├── QueueManagerForm.py   # Queue management
        └── SkillManagerForm.py   # Skill management
```

### Technology Stack
- **Frontend**: Anvil (Python + Material Design)
- **Backend**: Anvil Server (Python 3)
- **API**: Genesys Cloud Platform API
- **Authentication**: OAuth 2.0 Client Credentials

## 🤝 Contributing

This project is open source. To contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

For issues or questions:
- GitHub Issues: [Create an issue](https://github.com/adminlayers/admin-layers/issues)
- Documentation: See CLAUDE.md for development prompts
- Anvil Forum: https://anvil.works/forum

## 🎉 Quick Start

1. Create an Anvil account at https://anvil.works
2. Create a new blank app
3. Upload server code (genesys_api.py, demo_mode.py)
4. Create client forms (MainForm, LoginForm, UserManagerForm, etc.)
5. Set MainForm as startup form
6. Click Run
7. Try "Demo Mode" to explore features
8. Connect with Genesys OAuth credentials for production use

That's it! You now have a fully functional Genesys Cloud administration tool.
