# Admin Layers

**Local-first bulk admin tools for Genesys Cloud.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Admin Layers is a modular utility suite for Genesys Cloud administration. It runs locally on your machine, connects directly to Genesys Cloud APIs, and keeps your credentials secure.

🔗 **Website:** [adminlayers.com](https://adminlayers.com)

---

## Features

- **🚀 Bulk Operations** - Add hundreds of users to groups, assign skills, manage queues in seconds
- **🔒 Local-First Security** - Credentials never leave your machine. Direct API calls to Genesys Cloud.
- **👁️ Dry Run Mode** - Preview changes before executing. See the blast radius.
- **📦 Modular Design** - Use what you need. Extend with your own utilities.
- **📤 Import/Export** - CSV import, bulk export, seamless data movement

---

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Genesys Cloud OAuth credentials (Client Credentials grant)

### Installation

```bash
# Clone the repository
git clone https://github.com/adminlayers/admin-layers.git
cd admin-layers

# Install dependencies
pip install -r requirements.txt

# Set your credentials (choose one method)

# Option 1: Environment variables
export GENESYS_CLIENT_ID="your-client-id"
export GENESYS_CLIENT_SECRET="your-client-secret"
export GENESYS_REGION="mypurecloud.com"

# Option 2: Run setup wizard (Windows)
.\setup.ps1

# Start the application
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## Available Modules

| Module | Description | Status |
|--------|-------------|--------|
| **Group Manager** | Bulk group membership management | ✅ Available |
| **Skill Manager** | Bulk skill assignment and lookup | ✅ Available |
| **Queue Manager** | Queue membership and configuration | ✅ Available |

---

## Architecture

```
┌─────────────────────┐          ┌──────────────────────┐
│   YOUR COMPUTER     │          │   GENESYS CLOUD      │
│                     │          │                      │
│  ┌───────────────┐  │  HTTPS   │  ┌────────────────┐  │
│  │ Admin Layers  │──┼──────────┼─>│ Your Org Data  │  │
│  │ (This App)    │  │  Direct  │  │ (Users,Groups) │  │
│  └───────────────┘  │          │  └────────────────┘  │
│         │           │          │                      │
│         ▼           │          └──────────────────────┘
│  ┌───────────────┐  │
│  │ Your Keys     │  │  Credentials NEVER leave
│  │ (Local Env)   │  │  your machine
│  └───────────────┘  │
└─────────────────────┘
```

**Key Security Benefits:**
- Credentials stored locally as environment variables
- Direct API calls to Genesys Cloud (no proxy)
- No data passes through third-party servers
- Full audit trail in your Genesys Cloud org

---

## Project Structure

```
admin-layers/
├── app.py                  # Streamlit application entry point
├── requirements.txt        # Python dependencies
├── genesys_cloud/          # Core SDK
│   ├── __init__.py
│   ├── api.py              # API client with sub-APIs
│   ├── auth.py             # OAuth authentication
│   └── config.py           # Configuration management
├── utilities/              # Utility modules
│   ├── __init__.py
│   ├── base.py             # BaseUtility abstract class
│   ├── group_manager.py    # Group management utility
│   ├── skill_manager.py    # Skill management utility
│   └── queue_manager.py    # Queue management utility
├── .streamlit/
│   └── config.toml         # Streamlit theme
├── setup.ps1               # Windows setup wizard
└── start.ps1               # Windows start script
```

---

## Creating Custom Utilities

Admin Layers is designed to be extensible. Create your own utilities by extending `BaseUtility`:

```python
from utilities import BaseUtility, UtilityConfig

class MyUtility(BaseUtility):
    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="my_utility",
            name="My Utility",
            description="Does something useful",
            icon="🔧",
            category="Custom"
        )

    def render_sidebar(self) -> None:
        # Add sidebar controls
        pass

    def render_main(self) -> None:
        # Render main content
        pass
```

Then register it in `app.py`:

```python
UTILITIES = {
    "my_utility": MyUtility,
    # ... other utilities
}
```

See `utilities/TEMPLATE.py` for a complete template.

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GENESYS_CLIENT_ID` | Yes | OAuth Client ID |
| `GENESYS_CLIENT_SECRET` | Yes | OAuth Client Secret |
| `GENESYS_REGION` | No | Genesys region (default: `mypurecloud.com`) |

### Supported Regions

| Region | Domain |
|--------|--------|
| US East | `mypurecloud.com` |
| US West | `usw2.pure.cloud` |
| Canada | `cac1.pure.cloud` |
| EU Ireland | `mypurecloud.ie` |
| EU Frankfurt | `mypurecloud.de` |
| EU London | `euw2.pure.cloud` |
| Asia Pacific (Sydney) | `mypurecloud.com.au` |
| Asia Pacific (Tokyo) | `mypurecloud.jp` |
| Asia Pacific (Seoul) | `apne2.pure.cloud` |
| Asia Pacific (Mumbai) | `aps1.pure.cloud` |

---

## OAuth Client Setup

To use Admin Layers, you need a Genesys Cloud OAuth client with **Client Credentials** grant:

1. Go to **Genesys Cloud Admin** → **Integrations** → **OAuth**
2. Click **Add Client**
3. Set **Grant Type** to **Client Credentials**
4. Add required **Scopes** based on modules you'll use:
   - Groups: `groups`, `users:readonly`
   - Skills: `routing`, `users`
   - Queues: `routing:readonly`
5. Assign a **Role** with appropriate permissions
6. Save and copy the **Client ID** and **Client Secret**

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

Admin Layers is not affiliated with, endorsed by, or sponsored by Genesys. Genesys Cloud is a trademark of Genesys Telecommunications Laboratories, Inc.

---

## Support

- 📖 [Documentation](https://github.com/adminlayers/docs)
- 🐛 [Report Issues](https://github.com/adminlayers/admin-layers/issues)
- 💬 [Discussions](https://github.com/adminlayers/admin-layers/discussions)
