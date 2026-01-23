# Claude Code Prompts for Admin Layers

Copy these prompts to work with Claude Code on this project.

---

## 🚀 Getting Started

### Initialize the project
```
Review the .claude/instructions.md file to understand this project. 
Then check the current state of the codebase in core/ and utilities/.
Summarize what's implemented and what's missing.
```

---

## 🔧 Creating New Utilities

### Generate a Queue Manager utility
```
Create a new utility called QueueManagerUtility in utilities/queue_manager.py.

Follow the pattern in utilities/enhanced_group_manager.py but for queues:
- List/search queues
- View queue members (agents)
- Bulk add agents to queue with rollback support
- Bulk remove agents with rollback support
- Export queue members
- Show operation history

Use the existing self.api.queues methods from genesys_cloud/api.py.
Include impact assessment before bulk operations.
```

### Generate a Skills Manager utility
```
Create a SkillsManagerUtility in utilities/skills_manager.py.

Features needed:
- List all routing skills
- View users with a specific skill
- Bulk assign skill to multiple users (with proficiency setting)
- Bulk remove skill from users
- "Skill Gap Analysis" - compare required skills vs assigned skills
- Rollback support for all bulk operations

Use self.api.routing methods for skill operations.
```

### Generate a User Manager utility
```
Create a UserManagerUtility in utilities/user_manager.py.

Features:
- Search and list users
- View user details (profile, skills, groups, queues)
- Bulk activate users
- Bulk deactivate users
- Bulk update department/title
- Export user lists
- Rollback support

This should be a comprehensive user management tool.
```

---

## 🔄 Enhancing the Rollback System

### Add transaction support
```
Enhance core/rollback.py to support multi-operation transactions.

Requirements:
- Transaction class that groups multiple operations
- All-or-nothing rollback (if one fails, rollback all)
- Transaction isolation (capture state once for entire transaction)
- Transaction history view

Example usage:
with rollback.transaction("Move users between groups") as tx:
    tx.add_operation(remove_from_old_group)
    tx.add_operation(add_to_new_group)
# If either fails, both are rolled back
```

### Add scheduled rollback
```
Add the ability to schedule automatic rollback after a time period.

Use case: "Add these users to the group, but automatically remove them in 24 hours"

Add to core/rollback.py:
- ScheduledRollback class
- Storage for scheduled operations
- Check function to run on app startup
```

---

## 📊 Adding New Features

### Add audit dashboard
```
Create a new utility called AuditDashboardUtility in utilities/audit_dashboard.py.

This should show:
- All operations across all utilities
- Filter by date range, utility, operation type
- Success/failure statistics
- Charts showing operation volume over time
- Export audit log to CSV

Use the RollbackStorage to query operation history.
```

### Add diff viewer
```
Add a visual diff viewer to show before/after state changes.

Create core/diff_viewer.py with:
- Function to compare two ResourceState objects
- Generate human-readable diff output
- Streamlit component to render diff with color coding
- Support for nested object comparison

Integrate into the operation history view.
```

---

## 🏭 Factory Improvements

### Add API schema auto-detection
```
Enhance core/factory.py to auto-detect columns from Genesys API responses.

When generating a utility:
1. Make a sample API call to get one entity
2. Analyze the response structure
3. Auto-generate ColumnConfig for each field
4. Infer render type from field name/value (e.g., "state" → status-badge)

This reduces manual configuration needed for new utilities.
```

### Add validation rules generator
```
Add validation rule generation to the factory.

For import/create operations:
- Detect field types from API schema
- Generate Pydantic models for validation
- Add validation to import flows
- Show clear error messages for invalid data
```

---

## 🔌 API Enhancements

### Add Data Tables API
```
Add DataTablesAPI to genesys_cloud/api.py for Architect data tables.

Methods needed:
- list() - get all data tables
- get(table_id) - get table metadata
- get_rows(table_id) - get all rows with pagination
- add_row(table_id, data) - add a row
- update_row(table_id, row_key, data) - update a row
- delete_row(table_id, row_key) - delete a row
- import_rows(table_id, rows) - bulk import

Endpoints:
- /api/v2/flows/datatables
- /api/v2/flows/datatables/{datatableId}/rows
```

### Add Divisions API
```
Add DivisionsAPI to genesys_cloud/api.py.

Methods:
- list() - get all divisions
- get(division_id) - get division details
- create(name, description) - create division
- update(division_id, data) - update division
- get_users(division_id) - get users in division
- move_users(from_division, to_division, user_ids) - move users

Endpoint: /api/v2/authorization/divisions
```

---

## 📦 Open Source Preparation

### Prepare for open source release
```
Help me prepare this project for open source release.

1. Review all files for any hardcoded secrets or credentials
2. Create a proper .gitignore file
3. Create LICENSE file (MIT for core/, utilities/)
4. Create CONTRIBUTING.md with contribution guidelines
5. Create issue templates for bugs and feature requests
6. Create a GitHub Actions workflow for:
   - Linting (flake8)
   - Type checking (mypy)
   - Tests (pytest)
7. Update README.md with badges and clearer installation instructions
```

### Separate commercial features
```
Help me separate commercial features from open source.

1. Identify which features should be commercial:
   - Advanced rollback (transactions, scheduling)
   - Enterprise audit dashboard
   - SSO integration hooks
   - Priority support hooks

2. Create pro/ directory structure
3. Set up imports so pro/ extends core/ without modifying it
4. Create a license key validation system (simple, not DRM)
5. Update documentation to show free vs pro features
```

---

## 🧪 Testing

### Create test suite
```
Create a test suite for the core modules.

In tests/:
- test_rollback.py - test RollbackManager, StateCapture
- test_factory.py - test UtilityGenerator
- test_api.py - test API client with mocked responses

Use pytest and pytest-mock.
Create fixtures for common test data.
Mock all Genesys API calls.
```

### Create integration tests
```
Create integration tests that can run against a Genesys sandbox.

In tests/integration/:
- test_group_operations.py - test actual group membership changes
- test_rollback_live.py - test rollback with real API

These should:
- Use environment variables for credentials
- Clean up after themselves
- Be skipped if no credentials available
```

---

## 📚 Documentation

### Generate API documentation
```
Create comprehensive API documentation in docs/.

1. docs/api/rollback.md - RollbackManager API reference
2. docs/api/factory.md - UtilityGenerator API reference  
3. docs/api/base.md - BaseEnhancedUtility API reference
4. docs/guides/creating-utilities.md - Step-by-step guide
5. docs/guides/rollback-system.md - How rollback works

Use docstrings from the code and expand with examples.
```

### Create video script
```
Write a script for a 5-minute demo video of Admin Layers.

Cover:
1. Problem: Manual Genesys admin is tedious and risky
2. Solution: Admin Layers with rollback
3. Demo: Add users to group with preview
4. Demo: Oops! Rollback the change
5. Demo: Generate a new utility in minutes
6. Call to action: Star on GitHub, try it out
```

---

## 🐛 Debugging

### Debug rollback not working
```
The rollback feature isn't restoring state correctly.

Debug steps:
1. Check if before_state is being captured (add logging)
2. Verify the state is saved to SQLite correctly
3. Check if the rollback executor is finding the right members to restore
4. Test with a simple 1-user add/rollback

Show me the relevant code and add debug logging.
```

### Debug API authentication
```
Getting 401 errors from Genesys API.

Debug steps:
1. Check if token is being refreshed properly
2. Verify client credentials are correct
3. Check if region URL is correct
4. Add request/response logging to api.py

Help me trace through the auth flow.
```
