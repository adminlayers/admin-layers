# Deploying to Anvil from GitHub

This repository is now clean and ready to clone directly into Anvil.

## ✅ Repository Fixed

The following issues have been resolved:
- ✅ Removed old Streamlit/NiceGUI code (6,818 lines deleted)
- ✅ Removed conflicts and duplicate files
- ✅ Fixed YAML indentation error in MainForm.yaml
- ✅ Added proper Python package structure (__init__.py files)
- ✅ Moved Anvil app to root directory
- ✅ Clean, minimal structure ready for Anvil

## 📁 Current Structure

```
admin-layers/
├── anvil.yaml                    # Anvil app configuration
├── server_code/
│   ├── __init__.py
│   ├── genesys_api.py           # Genesys Cloud API wrapper
│   └── demo_mode.py             # Demo data for testing
└── client_code/
    ├── __init__.py
    └── forms/
        ├── __init__.py
        ├── _anvil_designer.py
        ├── MainForm.py          # Main layout
        ├── MainForm.yaml        # Form designer spec
        ├── LoginForm.py         # Authentication
        ├── UserManagerForm.py   # Users + BULK EDIT ⭐
        ├── GroupManagerForm.py  # Groups
        ├── QueueManagerForm.py  # Queues
        └── SkillManagerForm.py  # Skills
```

## 🚀 Clone from GitHub to Anvil

### Option 1: Clone via Anvil Git Integration (Recommended)

1. **Sign in to Anvil**
   - Go to https://anvil.works
   - Sign in to your account

2. **Create New App from Git**
   - Click "Create New App"
   - Select "Clone from Git Repository"
   - Enter your GitHub URL:
     ```
     https://github.com/adminlayers/admin-layers
     ```
   - Branch: `claude/bulk-edit-profiles-zvvoW`
   - Click "Clone"

3. **Wait for Import**
   - Anvil will read the files and create the app
   - This may take 30-60 seconds

4. **Set Startup Form**
   - After import, click the gear icon ⚙️
   - Settings → Startup Form → Select "MainForm"
   - Click Save

5. **Run the App**
   - Click the green Run button ▶️
   - Try "Demo Mode" first to test

### Option 2: Manual Copy (If Git Clone Fails)

If the Git clone has issues, you can manually copy the code:

1. **Create Blank App**
   - Anvil → Create New App → Start with Blank App
   - Name it "Admin Layers"

2. **Add Server Modules**

   **Module 1: genesys_api**
   - Server Code → + Add Module → Name: `genesys_api`
   - Copy contents of `server_code/genesys_api.py`
   - Paste into Anvil editor

   **Module 2: demo_mode**
   - Server Code → + Add Module → Name: `demo_mode`
   - Copy contents of `server_code/demo_mode.py`
   - Paste into Anvil editor

3. **Add Client Forms**

   Delete the default Form1, then create each form:

   **a. MainForm**
   - Forms → + Add Form → Name: `MainForm`
   - Design view: Add components from MainForm.yaml
   - Code view: Copy from `client_code/forms/MainForm.py`

   **b. LoginForm**
   - Forms → + Add Form → Name: `LoginForm`
   - Code view: Copy from `client_code/forms/LoginForm.py`

   **c. UserManagerForm**
   - Forms → + Add Form → Name: `UserManagerForm`
   - Code view: Copy from `client_code/forms/UserManagerForm.py`

   **d. GroupManagerForm**
   - Forms → + Add Form → Name: `GroupManagerForm`
   - Code view: Copy from `client_code/forms/GroupManagerForm.py`

   **e. QueueManagerForm**
   - Forms → + Add Form → Name: `QueueManagerForm`
   - Code view: Copy from `client_code/forms/QueueManagerForm.py`

   **f. SkillManagerForm**
   - Forms → + Add Form → Name: `SkillManagerForm`
   - Code view: Copy from `client_code/forms/SkillManagerForm.py`

4. **Configure App**
   - Settings (⚙️) → Startup Form → MainForm
   - Save

5. **Run**
   - Click Run ▶️
   - Test with Demo Mode

## 🧪 Testing

### Test Demo Mode First
1. Run the app
2. Click "Demo Mode" button
3. Navigate to "User Manager"
4. Click "Bulk Edit" tab
5. Paste sample CSV:
   ```csv
   email,title,department
   alice.johnson@acmecorp.com,Lead Agent,Support
   bob.martinez@acmecorp.com,Team Lead,Support
   ```
6. Click "Process CSV"
7. Verify preview shows correctly
8. Uncheck "Preview only" and process again

### Test Production Mode
1. Get Genesys OAuth credentials
2. Disconnect from demo mode
3. Enter Client ID, Secret, and Region
4. Click "Connect"
5. Test bulk edit with real users (start with 2-3 users)

## 🔧 Troubleshooting

### "Cannot find module" errors
- Make sure all forms are named exactly as shown (case-sensitive)
- Check that MainForm is set as startup form

### Import errors in forms
- Verify all forms are created
- Check that imports match form names

### YAML parsing errors
- The MainForm.yaml indentation has been fixed
- If you manually copy, ensure exact indentation

### "Not connected" errors
- Click "Demo Mode" or "Connect" before using utilities
- Check that OAuth credentials are valid

## 📊 What You Get

### Working Features
✅ OAuth authentication to Genesys Cloud
✅ Demo mode with sample data
✅ User Manager with list view
✅ **Bulk Edit Profiles via CSV** ⭐
  - Update name, department, title, state
  - Preview mode before applying
  - Detailed error reporting
✅ Group Manager with list view
✅ Queue Manager with list view
✅ Skill Manager with list view
✅ Mobile-responsive interface
✅ Material Design UI

### Coming Soon
- Bulk group membership changes
- Bulk queue assignments
- Bulk skill assignments
- Export to Excel
- Operation history/audit log

## 🆘 Still Having Issues?

If you're still getting errors after cloning:

1. **Check the GitHub repo**
   - Make sure you're on branch: `claude/bulk-edit-profiles-zvvoW`
   - Latest commit: "Clean up repository - Remove old code and keep only Anvil app"

2. **Try manual copy instead**
   - Use Option 2 above
   - Copy each file manually

3. **Check Anvil status**
   - https://status.anvil.works
   - Make sure Anvil services are operational

4. **Get help**
   - Anvil Forum: https://anvil.works/forum
   - GitHub Issues: https://github.com/adminlayers/admin-layers/issues

## 🎉 Success!

Once deployed, you'll have a permanent URL:
- `https://your-app-name.anvil.app`
- Works on desktop, mobile, tablet
- Share with your team
- Free tier supports multiple users

Enjoy your new Genesys Cloud admin tool!
