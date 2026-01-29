"""
Chat Assistant Utility
Provides a chat interface with multiple backend support:
- OpenRouter API (cloud models)
- Ollama (local models)
- LM Studio (local models)

Uses Streamlit's native chat components for standard UX.
"""

import base64
from typing import Any, Dict, List, Optional, Union

import requests
import streamlit as st

from core.encrypted_storage import get_storage
from utilities.base import BaseUtility, UtilityConfig

# =============================================================================
# Backend Configuration
# =============================================================================

BACKENDS = {
    "openrouter": {
        "name": "OpenRouter",
        "description": "Cloud API with 100+ models (Claude, GPT-4, Gemini, etc.)",
        "base_url": "https://openrouter.ai/api/v1",
        "requires_key": True,
        "default_models": [
            "anthropic/claude-sonnet-4",
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-4-turbo",
            "google/gemini-pro-1.5",
            "google/gemini-flash-1.5",
            "meta-llama/llama-3.1-70b-instruct",
            "meta-llama/llama-3.1-8b-instruct",
            "mistralai/mistral-large",
            "deepseek/deepseek-chat",
            "qwen/qwen-2.5-72b-instruct",
        ],
    },
    "ollama": {
        "name": "Ollama",
        "description": "Local models via Ollama (runs on your machine)",
        "base_url": "http://localhost:11434/v1",
        "requires_key": False,
        "default_models": [
            "llama3.2",
            "llama3.1",
            "mistral",
            "mixtral",
            "codellama",
            "phi3",
            "gemma2",
            "qwen2.5",
            "deepseek-coder-v2",
        ],
    },
    "lmstudio": {
        "name": "LM Studio",
        "description": "Local models via LM Studio server",
        "base_url": "http://localhost:1234/v1",
        "requires_key": False,
        "default_models": [
            "local-model",
        ],
    },
    "custom": {
        "name": "Custom OpenAI-Compatible",
        "description": "Any OpenAI-compatible API endpoint",
        "base_url": "",
        "requires_key": True,
        "default_models": [],
    },
}

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful AI assistant. Be concise and accurate in your responses."
)

DEFAULT_SETTINGS = {
    "backend": "openrouter",
    "model": "anthropic/claude-sonnet-4",
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "temperature": 0.7,
    "max_tokens": 4096,
    "top_p": 1.0,
    "custom_base_url": "",
}


class ChatAssistantUtility(BaseUtility):
    """Chat assistant with multi-backend support."""

    @classmethod
    def get_config(cls) -> UtilityConfig:
        return UtilityConfig(
            id="chat_assistant",
            name="Chat Assistant",
            description="AI chat with multiple backends",
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

        # Load saved settings
        saved = self.storage.retrieve_chat_settings() or {}
        defaults = DEFAULT_SETTINGS.copy()
        defaults.update(saved)

        for key, val in defaults.items():
            state_key = f"chat_{key}"
            if state_key not in st.session_state:
                st.session_state[state_key] = val

    def _get_base_url(self) -> str:
        """Get the base URL for the current backend."""
        backend = st.session_state.chat_backend
        if backend == "custom":
            return str(st.session_state.chat_custom_base_url or "")
        backend_config = BACKENDS.get(backend, {})
        return str(backend_config.get("base_url", ""))

    def _get_client(self):
        """Get OpenAI client configured for current backend."""
        try:
            from openai import OpenAI
        except ImportError:
            st.error("OpenAI package not installed. Run: pip install openai")
            return None

        backend = st.session_state.chat_backend
        base_url = self._get_base_url()

        if not base_url:
            st.error("No API endpoint configured")
            return None

        # Get API key if required
        api_key = "not-needed"
        if BACKENDS.get(backend, {}).get("requires_key", False):
            api_key = self.storage.retrieve_openrouter_key()
            if not api_key:
                return None

        return OpenAI(base_url=base_url, api_key=api_key)

    def _check_backend_status(self) -> Dict[str, Any]:
        """Check if the current backend is reachable."""
        backend = st.session_state.chat_backend
        base_url = self._get_base_url()

        if not base_url:
            return {"status": "error", "message": "No endpoint configured"}

        try:
            # Try to reach the models endpoint
            if backend == "ollama":
                resp = requests.get("http://localhost:11434/api/tags", timeout=3)
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    return {
                        "status": "ok",
                        "message": f"{len(models)} models available",
                        "models": [m.get("name") for m in models],
                    }
            else:
                resp = requests.get(f"{base_url}/models", timeout=5)
                if resp.status_code == 200:
                    return {"status": "ok", "message": "Connected"}
                elif resp.status_code == 401:
                    return {"status": "error", "message": "Invalid API key"}

            return {"status": "error", "message": f"HTTP {resp.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"status": "offline", "message": "Cannot connect"}
        except requests.exceptions.Timeout:
            return {"status": "timeout", "message": "Connection timeout"}
        except Exception as e:
            return {"status": "error", "message": str(e)[:50]}

    def _fetch_ollama_models(self) -> List[str]:
        """Fetch available models from Ollama."""
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=3)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                return [str(m.get("name", "")) for m in models if m.get("name")]
        except Exception:
            pass
        default_models = BACKENDS["ollama"]["default_models"]
        return list(default_models) if isinstance(default_models, list) else []

    def _chat_completion(
        self,
        messages: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Send messages and get response."""
        client = self._get_client()
        if not client:
            return None

        # Build messages with system prompt
        system_prompt = st.session_state.chat_system_prompt
        full_messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]
        full_messages.extend(messages)

        try:
            response = client.chat.completions.create(
                model=st.session_state.chat_model,
                messages=full_messages,
                temperature=st.session_state.chat_temperature,
                max_tokens=st.session_state.chat_max_tokens,
                top_p=st.session_state.chat_top_p,
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"API Error: {str(e)}")
            return None

    def _encode_image(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        """Encode image bytes to base64 data URL."""
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{mime_type};base64,{b64}"

    def _build_message_content(
        self,
        text: Optional[str] = None,
        images: Optional[List[Any]] = None,
        audio: Optional[Any] = None,
    ) -> Union[str, List[Dict[str, Any]]]:
        """Build message content, handling text, images, and audio."""
        # If only text, return simple string
        if not images and not audio:
            return text or ""

        # Build multimodal content array
        content: List[Dict[str, Any]] = []

        # Add text if present
        if text:
            content.append({"type": "text", "text": text})

        # Add images
        if images:
            for img in images:
                try:
                    img_bytes = img.read()
                    img.seek(0)  # Reset for display
                    mime = getattr(img, "type", "image/jpeg")
                    data_url = self._encode_image(img_bytes, mime)
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        }
                    )
                except Exception:
                    pass

        # Note about audio (most APIs don't support audio in chat)
        if audio:
            content.append(
                {
                    "type": "text",
                    "text": "[Audio attachment - transcription not available]",
                }
            )

        return content if content else ""

    def _save_settings(self):
        """Save current chat settings."""
        settings = {
            "backend": st.session_state.chat_backend,
            "model": st.session_state.chat_model,
            "system_prompt": st.session_state.chat_system_prompt,
            "temperature": st.session_state.chat_temperature,
            "max_tokens": st.session_state.chat_max_tokens,
            "top_p": st.session_state.chat_top_p,
            "custom_base_url": st.session_state.chat_custom_base_url,
        }
        self.storage.store_chat_settings(settings)

    def render_sidebar(self):
        """Render chat settings in sidebar."""
        st.markdown("**Chat Settings**")

        # Backend selection
        backend = st.selectbox(
            "Backend",
            options=list(BACKENDS.keys()),
            format_func=lambda x: BACKENDS[x]["name"],
            index=list(BACKENDS.keys()).index(st.session_state.chat_backend),
            key="sidebar_backend",
        )
        if backend != st.session_state.chat_backend:
            st.session_state.chat_backend = backend
            # Reset model when switching backends
            default_models = BACKENDS[backend]["default_models"]
            if default_models:
                st.session_state.chat_model = default_models[0]
            self._save_settings()
            st.rerun()

        # Status indicator
        status = self._check_backend_status()
        if status["status"] == "ok":
            st.success(f"● {status['message']}", icon="✓")
        elif status["status"] == "offline":
            st.error(f"○ {status['message']}", icon="✗")
        else:
            st.warning(f"◐ {status['message']}", icon="!")

        # Clear chat button
        if st.button("Clear Chat", use_container_width=True, key="sidebar_clear"):
            st.session_state.chat_messages = []
            st.rerun()

    def render_main(self):
        """Render main chat interface."""
        st.markdown("## Chat Assistant")

        # Check backend requirements
        backend = st.session_state.chat_backend
        backend_config = BACKENDS.get(backend, {})

        if backend_config.get("requires_key") and backend != "custom":
            api_key = self.storage.retrieve_openrouter_key()
            if not api_key:
                self._render_api_key_setup()
                return

        # Settings expander
        with st.expander("Settings", expanded=False):
            self._render_settings()

        # Status and model info
        col1, col2 = st.columns([2, 1])
        with col1:
            st.caption(
                f"**{backend_config.get('name', backend)}** · "
                f"`{st.session_state.chat_model}`"
            )
        with col2:
            status = self._check_backend_status()
            if status["status"] == "ok":
                st.caption("🟢 Connected")
            elif status["status"] == "offline":
                st.caption("🔴 Offline")
            else:
                st.caption(f"🟡 {status['message'][:20]}")

        # Chat messages display
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                self._render_message_content(msg)

        # Chat input with audio and file support
        prompt = st.chat_input(
            "Type a message, record audio, or attach an image...",
            accept_file=True,
            file_type=["jpg", "jpeg", "png", "gif", "webp"],
        )

        if prompt:
            # Extract components from prompt
            text = getattr(prompt, "text", None) or (
                prompt if isinstance(prompt, str) else None
            )
            files = prompt.get("files") if hasattr(prompt, "get") else None
            audio = getattr(prompt, "audio", None)

            # Build message content
            content = self._build_message_content(
                text=text,
                images=files,
                audio=audio,
            )

            # Store display data separately for rendering
            display_data = {
                "text": text,
                "images": files,
                "audio": audio,
            }

            # Add user message
            st.session_state.chat_messages.append(
                {
                    "role": "user",
                    "content": content,
                    "_display": display_data,
                }
            )

            # Display user message
            with st.chat_message("user"):
                self._render_user_input(text, files, audio)

            # Get assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = self._chat_completion(
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.chat_messages
                        ],
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
                    st.error(
                        "Failed to get response. Check your settings and connection."
                    )

    def _render_message_content(self, msg: Dict[str, Any]):
        """Render a message with support for multimodal content."""
        content = msg.get("content", "")
        display = msg.get("_display")

        if display:
            # Render with display data
            self._render_user_input(
                display.get("text"),
                display.get("images"),
                display.get("audio"),
            )
        elif isinstance(content, str):
            st.markdown(content)
        elif isinstance(content, list):
            # Multimodal content array
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        st.markdown(item.get("text", ""))
                    elif item.get("type") == "image_url":
                        url = item.get("image_url", {}).get("url", "")
                        if url.startswith("data:"):
                            st.image(url)

    def _render_user_input(
        self,
        text: Optional[str],
        images: Optional[List[Any]],
        audio: Optional[Any],
    ):
        """Render user input with text, images, and audio."""
        if text:
            st.markdown(text)
        if images:
            for img in images:
                try:
                    st.image(img, use_container_width=True)
                except Exception:
                    st.caption("📎 Image attachment")
        if audio:
            try:
                st.audio(audio)
            except Exception:
                st.caption("🎤 Audio recording")

    def _render_settings(self):
        """Render the settings panel."""
        backend = st.session_state.chat_backend
        backend_config = BACKENDS.get(backend, {})

        # Backend selection
        col1, col2 = st.columns(2)
        with col1:
            new_backend = st.selectbox(
                "Backend",
                options=list(BACKENDS.keys()),
                format_func=lambda x: BACKENDS[x]["name"],
                index=list(BACKENDS.keys()).index(backend),
                key="settings_backend",
                help=backend_config.get("description", ""),
            )
            if new_backend != backend:
                st.session_state.chat_backend = new_backend
                default_models = BACKENDS[new_backend]["default_models"]
                if default_models:
                    st.session_state.chat_model = default_models[0]
                self._save_settings()
                st.rerun()

        with col2:
            if backend_config.get("requires_key"):
                if st.button("Change API Key", key="change_key"):
                    self.storage.clear_openrouter_key()
                    st.rerun()

        # Custom endpoint for custom backend
        if backend == "custom":
            custom_url = st.text_input(
                "API Endpoint URL",
                value=st.session_state.chat_custom_base_url,
                placeholder="https://api.example.com/v1",
                key="custom_url_input",
            )
            if custom_url != st.session_state.chat_custom_base_url:
                st.session_state.chat_custom_base_url = custom_url
                self._save_settings()

        # Model selection
        st.markdown("---")
        st.markdown("**Model**")

        # Get model options
        if backend == "ollama":
            model_options = self._fetch_ollama_models()
        else:
            model_options = backend_config.get("default_models", []).copy()

        current_model = st.session_state.chat_model
        if current_model and current_model not in model_options:
            model_options.insert(0, current_model)

        col1, col2 = st.columns([2, 1])
        with col1:
            selected = st.selectbox(
                "Select model",
                options=model_options if model_options else [""],
                index=(
                    model_options.index(current_model)
                    if current_model in model_options
                    else 0
                ),
                label_visibility="collapsed",
                key="model_select",
            )

        with col2:
            custom_model = st.text_input(
                "Custom",
                placeholder="model-id",
                label_visibility="collapsed",
                key="custom_model",
            )

        final_model = custom_model if custom_model else selected
        if final_model and final_model != st.session_state.chat_model:
            st.session_state.chat_model = final_model
            self._save_settings()

        # Generation parameters
        st.markdown("---")
        st.markdown("**Generation Parameters**")

        col1, col2, col3 = st.columns(3)

        with col1:
            temp = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=float(st.session_state.chat_temperature),
                step=0.1,
                help="Higher = more creative, Lower = more focused",
                key="temp_slider",
            )
            if temp != st.session_state.chat_temperature:
                st.session_state.chat_temperature = temp
                self._save_settings()

        with col2:
            max_tok = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=32000,
                value=int(st.session_state.chat_max_tokens),
                step=100,
                help="Maximum response length",
                key="max_tokens_input",
            )
            if max_tok != st.session_state.chat_max_tokens:
                st.session_state.chat_max_tokens = max_tok
                self._save_settings()

        with col3:
            top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=float(st.session_state.chat_top_p),
                step=0.05,
                help="Nucleus sampling threshold",
                key="top_p_slider",
            )
            if top_p != st.session_state.chat_top_p:
                st.session_state.chat_top_p = top_p
                self._save_settings()

        # System prompt
        st.markdown("---")
        st.markdown("**System Prompt**")
        new_prompt = st.text_area(
            "System prompt",
            value=st.session_state.chat_system_prompt,
            height=100,
            label_visibility="collapsed",
            key="system_prompt_area",
        )
        if new_prompt != st.session_state.chat_system_prompt:
            st.session_state.chat_system_prompt = new_prompt
            self._save_settings()

        # Presets
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Reset to Defaults", use_container_width=True):
                for key, val in DEFAULT_SETTINGS.items():
                    st.session_state[f"chat_{key}"] = val
                self._save_settings()
                st.rerun()
        with col2:
            if st.button("Creative Mode", use_container_width=True):
                st.session_state.chat_temperature = 1.2
                st.session_state.chat_top_p = 0.95
                self._save_settings()
                st.rerun()
        with col3:
            if st.button("Precise Mode", use_container_width=True):
                st.session_state.chat_temperature = 0.3
                st.session_state.chat_top_p = 0.5
                self._save_settings()
                st.rerun()

    def _render_api_key_setup(self):
        """Render API key setup form."""
        backend = st.session_state.chat_backend
        backend_name = BACKENDS.get(backend, {}).get("name", backend)

        st.info(
            f"To use {backend_name}, you need an API key. "
            f"Get one at [openrouter.ai](https://openrouter.ai/keys)"
        )

        with st.form("api_key_setup"):
            api_key = st.text_input(
                "API Key",
                type="password",
                placeholder="sk-or-...",
            )

            if st.form_submit_button("Save API Key", use_container_width=True):
                if api_key:
                    self.storage.store_openrouter_key(api_key)
                    st.success("API key saved!")
                    st.rerun()
                else:
                    st.error("Please enter an API key")

        # Option to switch to local backend
        st.markdown("---")
        st.markdown("**Or use a local model:**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Use Ollama", use_container_width=True):
                st.session_state.chat_backend = "ollama"
                st.session_state.chat_model = "llama3.2"
                self._save_settings()
                st.rerun()
        with col2:
            if st.button("Use LM Studio", use_container_width=True):
                st.session_state.chat_backend = "lmstudio"
                st.session_state.chat_model = "local-model"
                self._save_settings()
                st.rerun()
