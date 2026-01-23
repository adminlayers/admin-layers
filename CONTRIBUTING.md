# Contributing to Admin Layers

First off, thank you for considering contributing to Admin Layers! It's people like you that make this tool useful for the Genesys Cloud community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by our commitment to providing a welcoming and inclusive environment. Please be respectful and constructive in all interactions.

## Getting Started

### What Can I Contribute?

- 🐛 **Bug Fixes** - Found a bug? We'd love a fix!
- 📝 **Documentation** - Improvements to docs, examples, or comments
- 🔧 **New Utilities** - Pre-built utilities for Genesys resources
- ✨ **Features** - Enhancements to the core framework
- 🧪 **Tests** - Improved test coverage

### What's Out of Scope?

- Features that require Genesys partner/premium access
- Changes to commercial components (`/pro`, `/enterprise`)
- Features that would compromise security

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip
- Git
- A Genesys Cloud sandbox (for integration testing)

### Setup Steps

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR-USERNAME/adminlayers.git
cd adminlayers

# 3. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev dependencies

# 5. Set up environment variables (for testing)
export GENESYS_CLIENT_ID=your-sandbox-client-id
export GENESYS_CLIENT_SECRET=your-sandbox-secret
export GENESYS_REGION=mypurecloud.com

# 6. Run tests to verify setup
pytest tests/
```

### Project Structure

```
adminlayers/
├── core/                    # Core framework (contribute here!)
│   ├── rollback.py          # Rollback engine
│   ├── base_enhanced.py     # Base utility class
│   └── factory.py           # Utility generator
├── utilities/               # Pre-built utilities (contribute here!)
├── genesys_cloud/           # Genesys API SDK
├── tests/                   # Test suite
├── docs/                    # Documentation
└── examples/                # Example code
```

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report, please check existing issues to avoid duplicates.

**Include in your bug report:**
- Python version
- Streamlit version
- Steps to reproduce
- Expected vs actual behavior
- Error messages/stack traces
- Screenshots if applicable

### Suggesting Features

Feature suggestions are welcome! Please include:
- Clear description of the feature
- Use case / problem it solves
- Proposed implementation (if you have ideas)
- Whether you're willing to implement it

### Creating a New Utility

New utilities are a great way to contribute! Here's how:

1. **Check if it exists** - Look in `utilities/` and open issues
2. **Open an issue first** - Describe the utility you want to create
3. **Follow the pattern** - Use `utilities/enhanced_group_manager.py` as reference
4. **Include tests** - Add tests in `tests/test_utilities/`
5. **Document it** - Add usage examples to the README

**Utility Requirements:**
- Must follow `BaseEnhancedUtility` pattern
- Must include rollback support for destructive operations
- Must have dry-run mode for bulk operations
- Must handle API errors gracefully

### Your First Pull Request

Not sure where to start? Look for issues labeled:
- `good first issue` - Simple, well-defined tasks
- `help wanted` - We'd especially appreciate help here
- `documentation` - Doc improvements (great for first-timers!)

## Pull Request Process

### Before Submitting

1. **Create an issue first** for significant changes
2. **Fork and branch** - Create a feature branch from `main`
3. **Follow style guidelines** - See below
4. **Add tests** - For new features or bug fixes
5. **Update docs** - If your change affects documentation
6. **Test locally** - Run the full test suite

### Branch Naming

```
feature/add-queue-manager
bugfix/rollback-not-saving
docs/improve-readme
```

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add QueueManagerUtility with bulk agent management

- Add queue search and list functionality
- Implement bulk add/remove agents with rollback
- Add queue member export
- Include impact assessment for bulk operations

Closes #42
```

Prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### PR Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have added tests for my changes
- [ ] All tests pass locally
- [ ] I have updated relevant documentation
- [ ] My commits are clean and well-described
- [ ] I have linked related issues

### Review Process

1. A maintainer will review your PR
2. They may request changes or ask questions
3. Once approved, it will be merged
4. Your contribution will be credited in the changelog

## Style Guidelines

### Python Style

We follow PEP 8 with some additions:

```python
# Use type hints
def get_members(self, group_id: str) -> List[Dict]:
    pass

# Use dataclasses for data structures
@dataclass
class UtilityConfig:
    id: str
    name: str
    
# Use descriptive variable names
user_ids_to_add = [u['id'] for u in users]  # Good
ids = [u['id'] for u in users]              # Too vague

# Document public methods
def render_impact_assessment(self, assessment: ImpactAssessment) -> bool:
    """
    Render impact assessment UI and get user confirmation.
    
    Args:
        assessment: ImpactAssessment to display
    
    Returns:
        True if user confirms, False otherwise
    """
```

### Streamlit UI Guidelines

```python
# Use consistent emoji conventions
st.markdown("## 👥 Group Manager")  # Page titles
st.button("➕ Add Members")          # Actions
st.success("✅ Operation complete")  # Success messages
st.error("❌ Operation failed")      # Error messages

# Always show feedback for operations
with st.spinner("Processing..."):
    result = do_operation()
if result.success:
    st.success("Done!")
else:
    st.error(f"Failed: {result.error}")

# Use columns for layout
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total", count)
```

### Testing Guidelines

```python
# Name tests descriptively
def test_rollback_membership_add_removes_added_members():
    pass

# Use fixtures for common setup
@pytest.fixture
def mock_api():
    return Mock(spec=GenesysCloudAPI)

# Test both success and failure cases
def test_add_members_success(mock_api):
    pass

def test_add_members_handles_api_error(mock_api):
    pass
```

## Questions?

- 💬 Open a [Discussion](https://github.com/yourusername/adminlayers/discussions)
- 🐛 Open an [Issue](https://github.com/yourusername/adminlayers/issues)
- 📧 Email: [your-email@example.com]

---

Thank you for contributing! 🎉
