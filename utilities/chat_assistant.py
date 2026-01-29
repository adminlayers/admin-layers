"""
Chat Assistant Utility
Provides a chat interface using OpenRouter API (OpenAI-compatible).
Uses Streamlit's native chat components for standard UX.
"""

from typing import Any, Dict, List, Optional

import streamlit as st

from core.encrypted_storage import get_storage
from utilities.base import BaseUtility, UtilityConfig

# Popular OpenRouter models - user can also type custom model IDs
POPULAR_MODELS = [
    "anthropic/claude-sonnet-4",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-haiku",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/gpt-4-turbo",
    "openai/gpt-3.5-turbo",
    "google/gemini-pro-1.5",
    "google/gemini-flash-1.5",
    "meta-llama/llama-3.1-70b-instruct",
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-large",
    "mistralai/mistral-medium",
    "deepseek/deepseek-chat",
]

DEFAULT_SYSTEM_PROMPT = (
    """You are a helpful AI assistant. Be concise and accurate in your responses."""
)


class ChatAssistantUtility(BaseUtility):
    """Chat assistant with OpenRouter API support."""

    @classmethod
    def get_config(cls) -> UtilityConfig:
        return UtilityConfig(
            name="Chat Assistant",
            description="AI chat with OpenRouter API",
            icon="💬",
            category="Tools",
        )

    def __init__(self, api: Any):
        super().__init__(api)
        self.storage = get_storage()
        self._init_chat_state()

    def _init_chat_state(self):
        """Initialize chat-related session state."""
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        if "chat_model" not in st.session_state:
            settings = self.storage.retrieve_chat_settings() or {}
            st.session_state.chat_model = settings.get(
                "model", "anthropic/claude-sonnet-4"
            )
        if "chat_system_prompt" not in st.session_state:
            settings = self.storage.retrieve_chat_settings() or {}
            st.session_state.chat_system_prompt = settings.get(
                "system_prompt", DEFAULT_SYSTEM_PROMPT
            )

    def _get_openrouter_client(self):
        """Get OpenAI client configured for OpenRouter."""
        try:
            from openai import OpenAI
        except ImportError:
            st.error("OpenAI package not installed. Run: pip install openai")
            return None

        api_key = self.storage.retrieve_openrouter_key()
        if not api_key:
            return None

        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def _chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        system_prompt: str,
    ) -> Optional[str]:
        """Send messages to OpenRouter and get response."""
        client = self._get_openrouter_client()
        if not client:
            return None

        # Build messages with system prompt
        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages.extend(messages)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=full_messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None

    def render_sidebar(self):
        """Render chat settings in sidebar."""
        st.markdown("**Chat Settings**")

        # Model selection
        current_model = st.session_state.chat_model
        model_options = POPULAR_MODELS.copy()
        if current_model and current_model not in model_options:
            model_options.insert(0, current_model)

        selected_model = st.selectbox(
            "Model",
            options=model_options,
            index=(
                model_options.index(current_model)
                if current_model in model_options
                else 0
            ),
            key="sidebar_model_select",
        )

        # Custom model input
        custom_model = st.text_input(
            "Or enter custom model ID",
            placeholder="provider/model-name",
            key="sidebar_custom_model",
        )

        if custom_model:
            selected_model = custom_model

        if selected_model != st.session_state.chat_model:
            st.session_state.chat_model = selected_model
            self._save_settings()

        # Clear chat button
        if st.button("Clear Chat", use_container_width=True, key="sidebar_clear"):
            st.session_state.chat_messages = []
            st.rerun()

    def _save_settings(self):
        """Save current chat settings."""
        self.storage.store_chat_settings(
            {
                "model": st.session_state.chat_model,
                "system_prompt": st.session_state.chat_system_prompt,
            }
        )

    def render_main(self):
        """Render main chat interface."""
        st.markdown("## Chat Assistant")

        # Check for API key
        api_key = self.storage.retrieve_openrouter_key()

        if not api_key:
            self._render_api_key_setup()
            return

        # Settings expander
        with st.expander("Settings", expanded=False):
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("**Model**")
                current_model = st.session_state.chat_model
                model_options = POPULAR_MODELS.copy()
                if current_model and current_model not in model_options:
                    model_options.insert(0, current_model)

                selected = st.selectbox(
                    "Select model",
                    options=model_options,
                    index=(
                        model_options.index(current_model)
                        if current_model in model_options
                        else 0
                    ),
                    label_visibility="collapsed",
                    key="main_model_select",
                )

                custom = st.text_input(
                    "Custom model ID",
                    placeholder="provider/model-name",
                    key="main_custom_model",
                )

                final_model = custom if custom else selected
                if final_model != st.session_state.chat_model:
                    st.session_state.chat_model = final_model
                    self._save_settings()

            with col2:
                st.markdown("**API Key**")
                if st.button("Change API Key", key="change_api_key"):
                    self.storage.clear_openrouter_key()
                    st.rerun()

            st.markdown("**System Prompt**")
            new_prompt = st.text_area(
                "System prompt",
                value=st.session_state.chat_system_prompt,
                height=100,
                label_visibility="collapsed",
                key="system_prompt_input",
            )
            if new_prompt != st.session_state.chat_system_prompt:
                st.session_state.chat_system_prompt = new_prompt
                self._save_settings()

        st.caption(f"Model: `{st.session_state.chat_model}`")

        # Chat messages display
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        if prompt := st.chat_input("Type your message..."):
            # Add user message
            st.session_state.chat_messages.append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = self._chat_completion(
                        messages=st.session_state.chat_messages,
                        model=st.session_state.chat_model,
                        system_prompt=st.session_state.chat_system_prompt,
                    )

                if response:
                    st.markdown(response)
                    st.session_state.chat_messages.append(
                        {
                            "role": "assistant",
                            "content": response,
                        }
                    )
                else:
                    st.error("Failed to get response. Check your API key and model.")

    def _render_api_key_setup(self):
        """Render API key setup form."""
        st.info(
            "To use the Chat Assistant, you need an OpenRouter API key. "
            "Get one at [openrouter.ai](https://openrouter.ai/keys)"
        )

        with st.form("openrouter_setup"):
            api_key = st.text_input(
                "OpenRouter API Key",
                type="password",
                placeholder="sk-or-...",
            )

            if st.form_submit_button("Save API Key", use_container_width=True):
                if api_key and api_key.startswith("sk-"):
                    self.storage.store_openrouter_key(api_key)
                    st.success("API key saved!")
                    st.rerun()
                else:
                    st.error("Please enter a valid OpenRouter API key")
