"""
Code Audit Report Utility
Interactive dashboard showing code quality issues, disconnected code,
incomplete implementations, and framework remnants.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from .base import BaseUtility, UtilityConfig


class IssueSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AuditIssue:
    """Represents a single audit finding."""

    id: str
    category: str
    severity: str
    file_path: str
    line_number: int
    title: str
    description: str
    recommendation: str
    code_snippet: str = ""


# =============================================================================
# AUDIT FINDINGS - Generated from code analysis
# =============================================================================

AUDIT_FINDINGS: List[Dict[str, Any]] = [
    # ==========================================================================
    # DISCONNECTED / UNUSED CODE
    # ==========================================================================
    {
        "id": "DISC-001",
        "category": "Disconnected Code",
        "severity": "low",
        "file_path": "utilities/TEMPLATE.py",
        "line_number": 1,
        "title": "Template utility not connected to application",
        "description": (
            "TEMPLATE.py defines TemplateUtility class but is not exported in "
            "__init__.py or registered in app.py UTILITIES dict. This file serves "
            "as documentation for creating new utilities but could be moved to a "
            "docs folder or marked more clearly as a template."
        ),
        "recommendation": (
            "Move to docs/utility_template.py or add a clearer filename like "
            "_TEMPLATE.py to indicate it's not meant to be imported."
        ),
        "code_snippet": "class TemplateUtility(BaseUtility):  # Not registered",
    },
    {
        "id": "DISC-002",
        "category": "Disconnected Code",
        "severity": "medium",
        "file_path": "utilities/history.py",
        "line_number": 1,
        "title": "ActionHistory module not integrated with utilities",
        "description": (
            "The history.py module provides ActionHistory and ActionRecord for "
            "audit trails and rollback, but none of the utilities (group_manager, "
            "queue_manager, skill_manager, user_manager) actually use it. "
            "The record_action() and get_rollback_data() functions are never called."
        ),
        "recommendation": (
            "Integrate history tracking into bulk operations. For example, "
            "in group_manager._execute_add(), call history.record_action() "
            "after successful add_members operations."
        ),
        "code_snippet": "# history.py:record_action() is never called by any utility",
    },
    {
        "id": "DISC-003",
        "category": "Disconnected Code",
        "severity": "low",
        "file_path": "app.py",
        "line_number": 707,
        "title": "Unused variable 'saved_profile'",
        "description": (
            "Variable saved_profile is assigned but never used in page_connect(). "
            "It's retrieved from storage but the value is not referenced anywhere."
        ),
        "recommendation": "Remove the unused assignment or use the variable as intended.",
        "code_snippet": "saved_profile = storage.retrieve_local_user()  # Never used",
    },
    # ==========================================================================
    # INCOMPLETE IMPLEMENTATIONS
    # ==========================================================================
    {
        "id": "INCMP-001",
        "category": "Incomplete Code",
        "severity": "medium",
        "file_path": "core/services.py",
        "line_number": 214,
        "title": "RoutingEndpoint protocol missing get_languages/get_wrapup_codes validation",
        "description": (
            "The validate_backend() function checks for routing methods but does "
            "not include get_languages and get_wrapup_codes in the validation list, "
            "even though they're defined in the RoutingEndpoint protocol."
        ),
        "recommendation": (
            "Add 'get_languages' and 'get_wrapup_codes' to the routing validation "
            "list in validate_backend() for complete protocol compliance checking."
        ),
        "code_snippet": (
            "# Missing from validation:\n" "# 'get_languages', 'get_wrapup_codes'"
        ),
    },
    {
        "id": "INCMP-002",
        "category": "Incomplete Code",
        "severity": "low",
        "file_path": "genesys_cloud/api.py",
        "line_number": 463,
        "title": "ConversationsAPI has limited implementation",
        "description": (
            "ConversationsAPI only implements get(), get_details(), disconnect(), "
            "and query(). The demo mode returns 'Not available' for all methods. "
            "This endpoint is not used by any utility."
        ),
        "recommendation": (
            "Either complete the implementation or remove if not needed. "
            "Consider adding a ConversationManagerUtility if analytics are needed."
        ),
        "code_snippet": "class ConversationsAPI:  # Not used by any utility",
    },
    {
        "id": "INCMP-003",
        "category": "Incomplete Code",
        "severity": "info",
        "file_path": "core/services.py",
        "line_number": 56,
        "title": "UsersEndpoint.list() method missing from validate_backend()",
        "description": (
            "The UsersEndpoint protocol defines list() generator method, but "
            "validate_backend() does not check for it. Only list_page() is validated."
        ),
        "recommendation": (
            "Add 'list' to the users validation list if this method is required, "
            "or document that list() is optional."
        ),
        "code_snippet": "# list() not in validation: ['get', 'search', ...]",
    },
    # ==========================================================================
    # UNUSED IMPORTS
    # ==========================================================================
    {
        "id": "IMPORT-001",
        "category": "Unnecessary Code",
        "severity": "low",
        "file_path": "genesys_cloud/config.py",
        "line_number": 8,
        "title": "Unused import: typing.Dict",
        "description": "Dict is imported from typing but never used in the module.",
        "recommendation": "Remove 'Dict' from the import statement.",
        "code_snippet": "from typing import Dict, Optional  # Dict unused",
    },
    {
        "id": "IMPORT-002",
        "category": "Unnecessary Code",
        "severity": "low",
        "file_path": "core/demo.py",
        "line_number": 13,
        "title": "Unused imports: datetime, timedelta",
        "description": (
            "datetime and timedelta are imported but not used. They may have "
            "been intended for timestamp generation but are not currently needed."
        ),
        "recommendation": "Remove unused imports from the import statement.",
        "code_snippet": "from datetime import datetime, timedelta  # Both unused",
    },
    {
        "id": "IMPORT-003",
        "category": "Unnecessary Code",
        "severity": "low",
        "file_path": "core/diagnostics.py",
        "line_number": 9,
        "title": "Unused import: typing.Dict",
        "description": "Dict is imported but never used in diagnostics.py.",
        "recommendation": "Remove 'Dict' from the import statement.",
        "code_snippet": "from typing import Any, Dict, List, Optional  # Dict unused",
    },
    {
        "id": "IMPORT-004",
        "category": "Unnecessary Code",
        "severity": "low",
        "file_path": "utilities/base.py",
        "line_number": 7,
        "title": "Unused imports: Dict, Optional",
        "description": "Dict and Optional are imported but not used in base.py.",
        "recommendation": "Remove unused types from the import statement.",
        "code_snippet": "from typing import Any, Dict, List, Optional  # Dict, Optional unused",
    },
    {
        "id": "IMPORT-005",
        "category": "Unnecessary Code",
        "severity": "low",
        "file_path": "utilities/group_manager.py",
        "line_number": 6,
        "title": "Unused imports: Dict, List",
        "description": "Dict and List are imported but not used in group_manager.py.",
        "recommendation": "Remove unused types from the import statement.",
        "code_snippet": "from typing import Dict, List  # Both unused",
    },
    {
        "id": "IMPORT-006",
        "category": "Unnecessary Code",
        "severity": "low",
        "file_path": "utilities/queue_manager.py",
        "line_number": 6,
        "title": "Unused imports: Dict, List, Optional",
        "description": "All type imports are unused in queue_manager.py.",
        "recommendation": "Remove the entire typing import line.",
        "code_snippet": "from typing import Dict, List, Optional  # All unused",
    },
    {
        "id": "IMPORT-007",
        "category": "Unnecessary Code",
        "severity": "low",
        "file_path": "utilities/skill_manager.py",
        "line_number": 6,
        "title": "Unused import: Optional",
        "description": "Optional is imported but not used in skill_manager.py.",
        "recommendation": "Remove 'Optional' from the import statement.",
        "code_snippet": "from typing import Dict, List, Optional  # Optional unused",
    },
    {
        "id": "IMPORT-008",
        "category": "Unnecessary Code",
        "severity": "low",
        "file_path": "utilities/user_manager.py",
        "line_number": 6,
        "title": "Unused imports: Dict, List, Optional",
        "description": "All type imports are unused in user_manager.py.",
        "recommendation": "Remove the entire typing import line.",
        "code_snippet": "from typing import Dict, List, Optional  # All unused",
    },
    # ==========================================================================
    # CODE QUALITY ISSUES
    # ==========================================================================
    {
        "id": "QUAL-001",
        "category": "Code Quality",
        "severity": "low",
        "file_path": "app.py",
        "line_number": 594,
        "title": "f-string without placeholders",
        "description": (
            "An f-string is used without any variable interpolation. "
            "This is unnecessary and should be a regular string."
        ),
        "recommendation": 'Change f"string" to "string" if no interpolation needed.',
        "code_snippet": 'f"Welcome to Admin Layers"  # No placeholders',
    },
    {
        "id": "QUAL-002",
        "category": "Code Quality",
        "severity": "low",
        "file_path": "genesys_cloud/auth.py",
        "line_number": 157,
        "title": "Bare except clause",
        "description": (
            "A bare 'except:' clause catches all exceptions including KeyboardInterrupt. "
            "This makes debugging harder and can hide real issues."
        ),
        "recommendation": "Replace 'except:' with 'except Exception:' at minimum.",
        "code_snippet": "except:  # Bare except - catches everything",
    },
    {
        "id": "QUAL-003",
        "category": "Code Quality",
        "severity": "info",
        "file_path": "core/demo.py",
        "line_number": 195,
        "title": "Random module used at module level with seed",
        "description": (
            "DEMO_USER_SKILLS uses random.Random() with user ID as seed at module load. "
            "This is intentional for reproducibility but could be documented better."
        ),
        "recommendation": "Add comment explaining the reproducible random pattern.",
        "code_snippet": "random.Random(user['id']).randint(1, 5)  # Reproducible",
    },
    # ==========================================================================
    # FRAMEWORK REMNANTS
    # ==========================================================================
    {
        "id": "REM-001",
        "category": "Framework Remnants",
        "severity": "info",
        "file_path": "utilities/base.py",
        "line_number": 31,
        "title": "Unused UtilityConfig fields",
        "description": (
            "UtilityConfig has requires_group, requires_queue, requires_user flags "
            "but these are not actually enforced anywhere in the codebase. "
            "They may have been planned for auto-selection features."
        ),
        "recommendation": (
            "Either implement the feature (auto-prompt for group/queue/user selection) "
            "or remove the unused config fields."
        ),
        "code_snippet": (
            "requires_group: bool = False  # Never checked\n"
            "requires_queue: bool = False  # Never checked\n"
            "requires_user: bool = False   # Never checked"
        ),
    },
    {
        "id": "REM-002",
        "category": "Framework Remnants",
        "severity": "info",
        "file_path": "CLAUDE.md",
        "line_number": 1,
        "title": "CLAUDE.md references non-existent rollback system",
        "description": (
            "CLAUDE.md contains prompts for enhancing 'core/rollback.py' with "
            "transactions and scheduled rollbacks, but no rollback.py file exists. "
            "The history.py module has basic rollback data but no RollbackManager."
        ),
        "recommendation": (
            "Either implement the rollback system as described, or update CLAUDE.md "
            "to reflect current architecture using history.py instead."
        ),
        "code_snippet": "# References: core/rollback.py (does not exist)",
    },
    {
        "id": "REM-003",
        "category": "Framework Remnants",
        "severity": "info",
        "file_path": "CLAUDE.md",
        "line_number": 1,
        "title": "CLAUDE.md references non-existent factory system",
        "description": (
            "CLAUDE.md contains prompts for 'core/factory.py' with UtilityGenerator "
            "for auto-generating utilities, but this file does not exist."
        ),
        "recommendation": (
            "Either implement the factory system or remove these prompts from CLAUDE.md."
        ),
        "code_snippet": "# References: core/factory.py (does not exist)",
    },
    # ==========================================================================
    # POTENTIAL ISSUES
    # ==========================================================================
    {
        "id": "POT-001",
        "category": "Potential Issue",
        "severity": "medium",
        "file_path": "core/encrypted_storage.py",
        "line_number": 400,
        "title": "Global singleton pattern may cause issues in testing",
        "description": (
            "EncryptedStorage uses a module-level singleton (_storage_instance). "
            "This can cause state leakage between tests and makes mocking harder."
        ),
        "recommendation": (
            "Consider using dependency injection or adding a reset_storage() "
            "function for testing purposes."
        ),
        "code_snippet": (
            "_storage_instance: Optional[EncryptedStorage] = None\n"
            "def get_storage() -> EncryptedStorage:  # Returns singleton"
        ),
    },
    {
        "id": "POT-002",
        "category": "Potential Issue",
        "severity": "medium",
        "file_path": "utilities/history.py",
        "line_number": 237,
        "title": "Global singleton pattern in history module",
        "description": (
            "ActionHistory also uses a module-level singleton that could cause "
            "similar issues to the storage singleton."
        ),
        "recommendation": "Add reset function or use dependency injection.",
        "code_snippet": "_history_instance: Optional[ActionHistory] = None",
    },
    {
        "id": "POT-003",
        "category": "Potential Issue",
        "severity": "low",
        "file_path": "core/demo.py",
        "line_number": 1,
        "title": "Demo data is mutable at module level",
        "description": (
            "DEMO_USERS, DEMO_GROUPS, DEMO_QUEUES, etc. are module-level lists "
            "that are mutated by DemoAPI operations (create, delete, add_members). "
            "Changes persist for the lifetime of the Python process."
        ),
        "recommendation": (
            "Consider deep-copying demo data on DemoAPI initialization to "
            "isolate test sessions, or accept this as intended demo behavior."
        ),
        "code_snippet": "DEMO_GROUPS.append(group)  # Mutates module-level list",
    },
    # ==========================================================================
    # TEST COVERAGE
    # ==========================================================================
    {
        "id": "TEST-001",
        "category": "Test Coverage",
        "severity": "medium",
        "file_path": "tests/",
        "line_number": 0,
        "title": "No tests for utility classes",
        "description": (
            "The tests directory only contains tests for core modules (demo, "
            "diagnostics, services). There are no tests for the utility classes "
            "(GroupManagerUtility, UserManagerUtility, etc.)."
        ),
        "recommendation": (
            "Add unit tests for utility classes. Focus on data transformation, "
            "state management, and API interaction mocking."
        ),
        "code_snippet": "# Missing: test_group_manager.py, test_user_manager.py, etc.",
    },
    {
        "id": "TEST-002",
        "category": "Test Coverage",
        "severity": "medium",
        "file_path": "tests/",
        "line_number": 0,
        "title": "No tests for encrypted_storage module",
        "description": (
            "The encrypted_storage.py module handles sensitive credential storage "
            "but has no tests to verify encryption/decryption, key derivation, "
            "or storage backends."
        ),
        "recommendation": (
            "Add tests for EncryptedStorage covering encrypt/decrypt, store/retrieve, "
            "and profile management functions."
        ),
        "code_snippet": "# Missing: test_encrypted_storage.py",
    },
    {
        "id": "TEST-003",
        "category": "Test Coverage",
        "severity": "low",
        "file_path": "tests/",
        "line_number": 0,
        "title": "No tests for GenesysCloudAPI",
        "description": (
            "The genesys_cloud/api.py module is not tested. While it requires "
            "mocking HTTP requests, basic request building and pagination logic "
            "should be tested."
        ),
        "recommendation": (
            "Add tests using pytest-mock or responses library to mock HTTP calls."
        ),
        "code_snippet": "# Missing: test_api.py with mocked requests",
    },
]


class AuditReportUtility(BaseUtility):
    """
    Code Audit Report Utility

    Displays findings from the comprehensive code audit including:
    - Disconnected/unused code
    - Incomplete implementations
    - Unnecessary code (unused imports)
    - Code quality issues
    - Framework remnants
    - Test coverage gaps
    """

    @staticmethod
    def get_config() -> UtilityConfig:
        return UtilityConfig(
            id="audit_report",
            name="Code Audit Report",
            description="Interactive code quality and audit findings dashboard",
            icon="📊",
            category="Tools",
            tags=["audit", "code quality", "report", "analysis"],
        )

    def init_state(self) -> None:
        if self.get_state("initialized") is None:
            self.set_state("initialized", True)
            self.set_state("filter_severity", "all")
            self.set_state("filter_category", "all")
            self.set_state("show_resolved", False)

    def render_sidebar(self) -> None:
        st.markdown("#### Filters")

        # Severity filter
        severities = ["all", "critical", "high", "medium", "low", "info"]
        severity = st.selectbox(
            "Severity",
            severities,
            index=severities.index(self.get_state("filter_severity", "all")),
            key="audit_severity_filter",
        )
        self.set_state("filter_severity", severity)

        # Category filter
        categories = ["all"] + sorted(set(f["category"] for f in AUDIT_FINDINGS))
        category = st.selectbox(
            "Category",
            categories,
            index=0,
            key="audit_category_filter",
        )
        self.set_state("filter_category", category)

        st.markdown("---")

        # Summary stats
        st.markdown("#### Summary")
        total = len(AUDIT_FINDINGS)
        by_severity = {}
        for f in AUDIT_FINDINGS:
            sev = f["severity"]
            by_severity[sev] = by_severity.get(sev, 0) + 1

        st.metric("Total Issues", total)
        for sev in ["critical", "high", "medium", "low", "info"]:
            if sev in by_severity:
                st.caption(f"{sev.capitalize()}: {by_severity[sev]}")

    def render_main(self) -> None:
        self.init_state()

        st.markdown("## 📊 Code Audit Report")
        st.caption("Generated from comprehensive codebase analysis")

        # Executive Summary
        self._render_executive_summary()

        st.markdown("---")

        # Findings by Category
        self._render_findings()

    def _render_executive_summary(self) -> None:
        """Render executive summary with metrics."""
        st.markdown("### Executive Summary")

        # Metrics row
        col1, col2, col3, col4, col5 = st.columns(5)

        findings = AUDIT_FINDINGS
        by_sev = {}
        for f in findings:
            sev = f["severity"]
            by_sev[sev] = by_sev.get(sev, 0) + 1

        col1.metric("Critical", by_sev.get("critical", 0))
        col2.metric("High", by_sev.get("high", 0))
        col3.metric("Medium", by_sev.get("medium", 0))
        col4.metric("Low", by_sev.get("low", 0))
        col5.metric("Info", by_sev.get("info", 0))

        # Category breakdown
        st.markdown("#### Issues by Category")

        by_cat = {}
        for f in findings:
            cat = f["category"]
            by_cat[cat] = by_cat.get(cat, 0) + 1

        df_cat = pd.DataFrame(
            [
                {"Category": cat, "Count": count}
                for cat, count in sorted(by_cat.items(), key=lambda x: -x[1])
            ]
        )

        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(df_cat, use_container_width=True, hide_index=True)
        with col2:
            st.markdown("""
            **Key Findings:**
            - ✅ All 20 tests pass
            - ✅ No syntax errors
            - ⚠️ Unused imports in 8 files
            - ⚠️ History module not integrated
            - ℹ️ CLAUDE.md references missing modules
            """)

    def _render_findings(self) -> None:
        """Render filterable findings list."""
        st.markdown("### Detailed Findings")

        # Get filter values
        sev_filter = self.get_state("filter_severity", "all")
        cat_filter = self.get_state("filter_category", "all")

        # Filter findings
        findings = AUDIT_FINDINGS
        if sev_filter != "all":
            findings = [f for f in findings if f["severity"] == sev_filter]
        if cat_filter != "all":
            findings = [f for f in findings if f["category"] == cat_filter]

        st.caption(f"Showing {len(findings)} of {len(AUDIT_FINDINGS)} findings")

        # Tabs by category
        if cat_filter == "all":
            categories = sorted(set(f["category"] for f in findings))
            if categories:
                tabs = st.tabs(categories)
                for tab, cat in zip(tabs, categories):
                    with tab:
                        cat_findings = [f for f in findings if f["category"] == cat]
                        self._render_finding_cards(cat_findings)
        else:
            self._render_finding_cards(findings)

    def _render_finding_cards(self, findings: List[Dict]) -> None:
        """Render finding cards."""
        for f in findings:
            severity_colors = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🔵",
                "info": "⚪",
            }
            icon = severity_colors.get(f["severity"], "⚪")

            with st.expander(f"{icon} [{f['id']}] {f['title']}", expanded=False):
                col1, col2 = st.columns([1, 3])

                with col1:
                    st.markdown(f"**Severity:** {f['severity'].upper()}")
                    st.markdown(f"**Category:** {f['category']}")
                    if f["line_number"] > 0:
                        st.markdown(
                            f"**Location:** {f['file_path']}:{f['line_number']}"
                        )
                    else:
                        st.markdown(f"**Location:** {f['file_path']}")

                with col2:
                    st.markdown("**Description:**")
                    st.markdown(f["description"])

                st.markdown("---")

                st.markdown("**Recommendation:**")
                st.info(f["recommendation"])

                if f["code_snippet"]:
                    st.markdown("**Code Reference:**")
                    st.code(f["code_snippet"], language="python")


# Export for registration
__all__ = ["AuditReportUtility"]
