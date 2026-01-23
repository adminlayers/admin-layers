"""
[Utility Name]
[Brief description of what this utility does.]

Copy this template to create new utilities:
1. Copy this file and rename it (e.g., queue_manager.py)
2. Replace all [placeholders] with your values
3. Update utilities/__init__.py to export your class
4. Register in app.py UTILITIES dict
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional, Any

from .base import BaseUtility, UtilityConfig


class TemplateUtility(BaseUtility):
    """
    [Utility Name]

    Features:
    - [Feature 1]
    - [Feature 2]
    - [Feature 3]

    Usage:
        # This utility is loaded automatically when registered in app.py
        # Users select it from the sidebar navigation
    """

    # =========================================================================
    # Configuration
    # =========================================================================

    @staticmethod
    def get_config() -> UtilityConfig:
        """
        Define utility metadata.

        Returns:
            UtilityConfig with utility settings
        """
        return UtilityConfig(
            id="template_utility",           # Unique ID (snake_case)
            name="Template Utility",         # Display name
            description="Template for new utilities",  # Short description
            icon="ðŸ”§",                       # Emoji icon
            category="General",              # Category for sidebar grouping
            requires_group=False,            # Set True if utility needs group selection
            requires_queue=False,            # Set True if utility needs queue selection
            requires_user=False,             # Set True if utility needs user selection
            tags=["template", "example"]     # Searchable tags
        )

    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    def init_state(self) -> None:
        """
        Initialize session state for this utility.

        Called once when utility is first loaded.
        Use get_state/set_state for utility-scoped state.
        """
        # Initialize state only once
        if self.get_state('initialized') is None:
            self.set_state('initialized', True)
            self.set_state('page', 'main')      # Current page/view
            self.set_state('data', [])          # Loaded data
            self.set_state('selected', None)    # Selected item

    def cleanup(self) -> None:
        """
        Clean up when switching away from this utility.

        Override to release resources or clear temporary state.
        """
        pass

    # =========================================================================
    # Sidebar Rendering
    # =========================================================================

    def render_sidebar(self) -> None:
        """
        Render sidebar controls for this utility.

        Add navigation, filters, and actions here.
        """
        # Section header
        st.markdown("#### Controls")

        # Example: Resource selection
        resource_id = st.text_input(
            "Resource ID",
            value=self.get_state('resource_id', ''),
            placeholder="Enter ID...",
            key=f"{self.get_config().id}_resource_input"
        )

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Load", use_container_width=True, key=f"{self.get_config().id}_load"):
                self._load_resource(resource_id)
        with col2:
            if st.button("Clear", use_container_width=True, key=f"{self.get_config().id}_clear"):
                self._clear_resource()

        # Example: Search expander
        with st.expander("Search"):
            query = st.text_input(
                "Search",
                placeholder="Search...",
                key=f"{self.get_config().id}_search",
                label_visibility="collapsed"
            )
            if query:
                self._render_search_results(query)

        st.markdown("---")

        # Navigation buttons
        st.markdown("#### Views")

        has_data = self.get_state('data') is not None and len(self.get_state('data', [])) > 0

        if st.button("Main View", use_container_width=True, key=f"{self.get_config().id}_nav_main"):
            self.set_state('page', 'main')
            st.rerun()

        if st.button("Action View", use_container_width=True, disabled=not has_data,
                     key=f"{self.get_config().id}_nav_action"):
            self.set_state('page', 'action')
            st.rerun()

        if st.button("Export", use_container_width=True, disabled=not has_data,
                     key=f"{self.get_config().id}_nav_export"):
            self.set_state('page', 'export')
            st.rerun()

    def _render_search_results(self, query: str) -> None:
        """Render search results in sidebar."""
        # Example: Search using API
        # results = self.api.users.search(query)
        # for item in results[:5]:
        #     if st.button(item.get('name'), key=f"search_{item.get('id')}"):
        #         self._load_resource(item.get('id'))

        st.caption(f"Searching for: {query}")
        st.caption("(Implement search logic)")

    # =========================================================================
    # Main Content Rendering
    # =========================================================================

    def render_main(self) -> None:
        """
        Render main content area.

        Routes to appropriate page based on state.
        """
        self.init_state()

        # Route to current page
        page = self.get_state('page', 'main')

        if page == 'main':
            self._render_main_page()
        elif page == 'action':
            self._render_action_page()
        elif page == 'export':
            self._render_export_page()
        else:
            self._render_main_page()

    def _render_main_page(self) -> None:
        """Render the main/default page."""
        config = self.get_config()
        data = self.get_state('data', [])

        st.markdown(f"## {config.name}")

        if not data:
            st.info("Enter a resource ID in the sidebar to begin.")
            self._render_getting_started()
            return

        # Example: Display data info
        st.caption(f"{len(data)} items loaded")

        # Toolbar
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Refresh"):
                self._refresh_data()
        with col2:
            if st.button("Clear"):
                self._clear_resource()

        # Filter
        search = st.text_input("Filter", placeholder="Type to filter...")

        # Build dataframe
        df = self._build_dataframe(data)

        # Apply filter
        if search and not df.empty:
            mask = df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
            df = df[mask]

        # Display
        st.caption(f"Showing {len(df)} items")
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)

    def _render_action_page(self) -> None:
        """Render action page (create/update/delete operations)."""
        st.markdown("## Actions")

        data = self.get_state('data', [])
        st.caption(f"Working with {len(data)} items")

        # Example: Tabs for different actions
        tab1, tab2 = st.tabs(["Add", "Remove"])

        with tab1:
            st.markdown("### Add Items")
            input_text = st.text_area(
                "Enter items (one per line)",
                height=150,
                placeholder="item1\nitem2\nitem3",
                key=f"{self.get_config().id}_add_input"
            )

            col1, col2 = st.columns(2)
            with col1:
                dry_run = st.checkbox("Preview only", value=True)
            with col2:
                if st.button("Process", type="primary", use_container_width=True):
                    if input_text:
                        self._process_add(input_text, dry_run)

        with tab2:
            st.markdown("### Remove Items")
            st.warning("Select items to remove")
            # Implement remove logic

    def _render_export_page(self) -> None:
        """Render export page."""
        st.markdown("## Export")

        data = self.get_state('data', [])
        st.caption(f"{len(data)} items available for export")

        df = self._build_dataframe(data)

        st.markdown("### Download Options")

        col1, col2 = st.columns(2)

        with col1:
            csv_data = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                data=csv_data,
                file_name="export.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            json_data = df.to_json(orient='records', indent=2)
            st.download_button(
                "Download JSON",
                data=json_data,
                file_name="export.json",
                mime="application/json",
                use_container_width=True
            )

        st.markdown("### Preview")
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)

    def _render_getting_started(self) -> None:
        """Render getting started help."""
        with st.expander("Getting Started"):
            st.markdown("""
            **How to use this utility:**

            1. Enter a resource ID in the sidebar
            2. Click "Load" to fetch data
            3. Use the views to manage data
            4. Export results when done

            **Tips:**
            - Use the search to find resources
            - Preview changes before applying
            """)

    # =========================================================================
    # Data Operations
    # =========================================================================

    def _load_resource(self, resource_id: str) -> None:
        """Load a resource by ID."""
        if not resource_id:
            self.show_warning("Enter a resource ID")
            return

        with st.spinner("Loading..."):
            # Example: Load from API
            # response = self.api.groups.get(resource_id)
            # if response.success:
            #     self.set_state('resource_id', resource_id)
            #     self.set_state('resource_info', response.data)
            #     members = self.api.groups.get_members(resource_id)
            #     self.set_state('data', members)
            #     st.rerun()
            # else:
            #     self.show_error(f"Failed to load: {response.error}")

            # Placeholder implementation
            self.set_state('resource_id', resource_id)
            self.set_state('data', [
                {'id': '1', 'name': 'Item 1', 'status': 'Active'},
                {'id': '2', 'name': 'Item 2', 'status': 'Active'},
                {'id': '3', 'name': 'Item 3', 'status': 'Inactive'},
            ])
            self.show_success(f"Loaded resource: {resource_id}")
            st.rerun()

    def _clear_resource(self) -> None:
        """Clear current resource selection."""
        self.set_state('resource_id', '')
        self.set_state('resource_info', None)
        self.set_state('data', [])
        self.set_state('page', 'main')
        st.rerun()

    def _refresh_data(self) -> None:
        """Refresh current data."""
        resource_id = self.get_state('resource_id')
        if resource_id:
            self._load_resource(resource_id)

    def _build_dataframe(self, data: List[Dict]) -> pd.DataFrame:
        """
        Build a DataFrame from data.

        Customize columns based on your data structure.
        """
        if not data:
            return pd.DataFrame()

        return pd.DataFrame([{
            'Name': item.get('name', 'Unknown'),
            'Status': item.get('status', 'N/A'),
            'ID': item.get('id', '')
        } for item in data])

    def _process_add(self, input_text: str, dry_run: bool) -> None:
        """Process adding items."""
        # Parse input
        items = [
            line.strip()
            for line in input_text.split('\n')
            if line.strip()
        ]

        if not items:
            self.show_error("No valid items found")
            return

        st.markdown("### Processing")
        progress = st.progress(0)

        results = {'success': [], 'failed': []}

        for i, item in enumerate(items):
            progress.progress((i + 1) / len(items))

            # Validate/process item
            # Example: Look up user by email
            # user = self.api.users.search_by_email(item)
            # if user:
            #     results['success'].append({'item': item, 'data': user})
            # else:
            #     results['failed'].append(item)

            # Placeholder
            results['success'].append({'item': item, 'data': {'id': str(i)}})

        # Show results
        col1, col2 = st.columns(2)

        with col1:
            self.show_success(f"Valid: {len(results['success'])}")
            for r in results['success']:
                st.caption(f"OK: {r['item']}")

        with col2:
            if results['failed']:
                self.show_error(f"Failed: {len(results['failed'])}")
                for item in results['failed']:
                    st.caption(f"X: {item}")

        # Execute if not dry run
        if results['success'] and not dry_run:
            st.markdown("---")
            # Execute the operation
            # response = self.api.groups.add_members(...)
            self.show_success(f"Added {len(results['success'])} items")
            self._refresh_data()
        elif results['success'] and dry_run:
            self.show_info("Preview complete. Uncheck 'Preview only' to execute.")
