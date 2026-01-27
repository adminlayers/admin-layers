# ⚡ Quick Start Guide - Anvil Admin Layers

Get your Genesys Cloud admin tool running in 10 minutes!

## Step 1: Create Anvil Account (2 minutes)

1. Go to https://anvil.works
2. Click "Sign Up" → Free plan is perfect
3. Verify your email

## Step 2: Create New App (1 minute)

1. Click "Create New App"
2. Select "Start with Blank App"
3. Name it: **Admin Layers**

## Step 3: Upload Server Code (3 minutes)

### Add genesys_api module:
1. Click "Server Code" in left sidebar
2. Click "+" button
3. Name: `genesys_api`
4. Open `server_code/genesys_api.py` from this folder
5. Copy ALL the code
6. Paste into Anvil editor
7. Anvil auto-saves ✓

### Add demo_mode module:
1. Click "+" again
2. Name: `demo_mode`
3. Open `server_code/demo_mode.py`
4. Copy and paste into Anvil

## Step 4: Create Forms (4 minutes)

### Delete default form:
1. Right-click "Form1" → Delete

### Add MainForm:
1. Click "+" next to Forms
2. Name: `MainForm`
3. Click "Code" tab at top
4. Open `client_code/forms/MainForm.py`
5. Copy ALL code
6. Paste into Anvil (replacing template code)

### Add other forms (repeat for each):
1. LoginForm
2. UserManagerForm
3. GroupManagerForm
4. QueueManagerForm
5. SkillManagerForm

**For each form:**
- Click "+" next to Forms
- Name it exactly as shown
- Switch to Code tab
- Copy from `client_code/forms/[FormName].py`
- Paste into Anvil

## Step 5: Configure & Run (30 seconds)

1. Click gear icon ⚙️ (top right)
2. "App Settings"
3. "Startup Form" → Select `MainForm`
4. Click "Save"
5. Click green "Run" button ▶️

## Step 6: Test Demo Mode (30 seconds)

1. You should see the login screen
2. Click "**Demo Mode**" button (orange)
3. Click "User Manager"
4. Click "Bulk Edit" tab
5. Paste this sample CSV:

```csv
email,title,department
alice.johnson@acmecorp.com,Lead Agent,Support
bob.martinez@acmecorp.com,Senior Team Lead,Support
```

6. Click "Process CSV"
7. See preview of changes ✓

## Step 7: Connect to Your Genesys (Production)

### Get OAuth Credentials:
1. Log into Genesys Cloud
2. Admin → Integrations → OAuth
3. "Add Client"
4. Grant type: **Client Credentials**
5. Roles: Select User, Group, Queue, Routing permissions
6. Save → Copy Client ID & Secret

### Connect in App:
1. Disconnect from demo mode
2. Paste Client ID
3. Paste Client Secret
4. Select your region
5. Click "Connect"

## 🎉 Done!

You now have:
- ✅ Full Genesys Cloud admin tool
- ✅ Bulk user profile editing
- ✅ Group, queue, skill management
- ✅ Demo mode for testing
- ✅ Mobile-friendly interface

## 📱 Access Anywhere

Your Anvil app has a permanent URL:
- `https://your-app-name.anvil.app`
- Works on desktop, tablet, mobile
- Share with your team

## 🔥 Pro Tips

### 1. Publish Your App
- Click "Publish" button (top right)
- Get permanent URL
- Share with team

### 2. Use Demo Mode for Training
- Train users without touching production
- Safe to experiment

### 3. Bulk Edit Best Practices
- **Always use "Preview only" first**
- Start with small batches (10-20 users)
- Keep CSV files as backups
- Export current data before bulk changes

### 4. Create Your Own CSV Templates
Excel/Google Sheets format:
```
| email                          | title         | department |
|--------------------------------|---------------|------------|
| user1@company.com              | Senior Agent  | Support    |
| user2@company.com              | Team Lead     | Support    |
```

Save as CSV → Upload

## 🆘 Need Help?

### Common Issues:

**"Module not found" error**
- Make sure all forms are named exactly as shown
- Check spelling and capitalization

**"Not connected" when clicking utilities**
- Click "Demo Mode" or "Connect" first
- Green "Connected" should show in navbar

**CSV not working**
- Check first row has: `email,title,department` (or your fields)
- No spaces in header names
- One header row, then data rows

### Get Support:
- Check README.md for detailed docs
- Anvil Forum: https://anvil.works/forum
- GitHub Issues: Open an issue with your question

## 🚀 What's Next?

### Enhance Your App:
1. **Add more bulk operations**
   - Bulk group assignments
   - Bulk skill assignments
   - Bulk queue membership

2. **Add reporting**
   - Export to Excel
   - Operation history
   - Audit logs

3. **Customize appearance**
   - App Settings → Theme
   - Change colors, fonts
   - Add your company logo

4. **Add authentication**
   - App Settings → Enable Users service
   - Add login requirement
   - Track who made changes

### Share Your Success:
- Star the GitHub repo
- Share on LinkedIn
- Tell your Genesys community

---

**Total time:** ~10 minutes
**Skill level:** Anyone who can copy/paste
**Cost:** Free (Anvil free tier)

Enjoy your new admin tool! 🎊
