import streamlit as st
import os
from pathlib import Path
import sys
import traceback

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from services.config_service import AppConfig
from services.llm_service import LLMService
from services.prompt_builder import PromptBuilder, Profile
from services.logging_utils import log
import pyperclip

def mask_key(key):
    if not key or len(key) < 8:
        return "***"
    return key[:4] + "..." + key[-4:]

# Page configuration
st.set_page_config(
    page_title="OutboundOwl - AI Email Assistant",
    page_icon="🦉",
    layout="wide"
)

def initialize_services():
    """Initialize the configuration and services."""
    config = AppConfig()
    log(f"Loaded config: provider={config.provider}, model={config.openai_model}, api_key={mask_key(config.openai_api_key)}")
    if not config.validate():
        st.error("⚠️ OpenAI API key is required. Please set it in the sidebar.")
        log("ERROR: OpenAI API key is missing or invalid.")
        return None, None, None
    try:
        llm_service = LLMService(config)
        prompt_builder = PromptBuilder(llm_service)
        return config, llm_service, prompt_builder
    except Exception as e:
        st.error(f"❌ Failed to initialize services: {e}")
        log(f"ERROR initializing services: {e}\n{traceback.format_exc()}")
        return None, None, None

def render_configuration_sidebar(config):
    """Render the configuration sidebar."""
    st.sidebar.title("⚙️ Configuration")
    
    # Provider selection (currently only OpenAI)
    st.sidebar.subheader("Model Provider")
    provider = st.sidebar.selectbox(
        "Provider",
        ["OpenAI"],
        help="Currently only OpenAI is supported"
    )
    
    # Model selection
    st.sidebar.subheader("Model")
    model = st.sidebar.selectbox(
        "Model",
        ["gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo"],
        index=1,  # Default to gpt-4-turbo-preview
        help="Select the OpenAI model to use"
    )
    
    # API Key input
    st.sidebar.subheader("API Key")
    api_key = st.sidebar.text_input(
        "OpenAI API Key",
        type="password",
        value=config.openai_api_key or "",
        help="Your OpenAI API key. You can also set this in the .env file."
    )
    
    # Update configuration if changed
    if api_key != config.openai_api_key:
        config.set("OPENAI_API_KEY", api_key)
        log(f"API key updated: {mask_key(api_key)}")
    if model != config.openai_model:
        config.set("OPENAI_MODEL", model)
        log(f"Model updated: {model}")
    
    # Tone and language settings
    st.sidebar.subheader("Email Settings")
    tone = st.sidebar.selectbox(
        "Default Tone",
        ["professional", "casual", "friendly", "formal"],
        help="Default tone for generated emails"
    )
    language = st.sidebar.selectbox(
        "Language",
        ["English", "Spanish", "French", "German"],
        help="Language for generated emails"
    )
    
    # Update configuration
    config.set("DEFAULT_TONE", tone)
    config.set("DEFAULT_LANGUAGE", language)
    
    return config

def render_chat_interface(prompt_builder):
    """Render the main chat interface."""
    st.title("OutboundOwl: Generate Outreach Emails For Any Use Case")
    st.markdown("Chat with me to create personalized outreach emails! Just describe your goal and I'll generate a draft.")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state['chat_history'] = []
    
    # Display chat messages
    for msg in st.session_state['chat_history']:
        st.chat_message(msg['role']).write(msg['content'])
    
    # Remove question mode block (no longer needed)
    # Chat input
    if user_input := st.chat_input("Describe your outreach goal or give feedback on the draft..."):
        log(f"User message: {user_input}", prefix="OutboundOwl")
        st.session_state['chat_history'].append({'role': 'user', 'content': user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        prompt_builder.add_message(user_input)
        draft = prompt_builder.get_draft_email()
        if draft:
            st.session_state['chat_history'].append({'role': 'assistant', 'content': draft})
            st.chat_message('assistant').write(draft)
            st.button("Copy to Clipboard", on_click=lambda: st.success("Copied!"))
            st.button("Regenerate", on_click=lambda: prompt_builder.add_message(user_input))
        else:
            st.session_state['chat_history'].append({'role': 'assistant', 'content': "I'm not sure how to respond. Please try again."})
            st.chat_message('assistant').write("I'm not sure how to respond. Please try again.")

def render_email_actions(email_content):
    """Render actions for the generated email."""
    st.markdown("---")
    st.subheader("📧 Email Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Copy to Clipboard", type="primary"):
            try:
                pyperclip.copy(email_content)
                st.success("✅ Email copied to clipboard!")
            except Exception as e:
                st.error(f"❌ Failed to copy: {e}")
                log(f"ERROR copying to clipboard: {e}", prefix="OutboundOwl")
    
    with col2:
        if st.button("🔄 Regenerate"):
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Conversation"):
            st.session_state['chat_history'] = []
            st.rerun()
    
    # Show email in expandable section
    with st.expander("📄 View Full Email"):
        st.text_area("Generated Email", email_content, height=400)

def render_context_display(prompt_builder):
    """Display the current extracted context."""
    if st.sidebar.checkbox("🔍 Show Extracted Context"):
        st.sidebar.subheader("Extracted Context")
        context = prompt_builder.get_context()
        
        st.sidebar.write(f"**Your Name:** {context.your_name or 'Not specified'}")
        st.sidebar.write(f"**Your Title:** {context.your_title or 'Not specified'}")
        st.sidebar.write(f"**Company:** {context.company_name or 'Not specified'}")
        st.sidebar.write(f"**Recipient:** {context.recipient_name or 'Not specified'}")
        st.sidebar.write(f"**Organization:** {context.recipient_organization or 'Not specified'}")
        st.sidebar.write(f"**Email Type:** {context.email_type}")
        st.sidebar.write(f"**Tone:** {context.tone}")
        st.sidebar.write(f"**Language:** {context.language}")
        
        if context.value_propositions:
            st.sidebar.write("**Value Propositions:**")
            for i, prop in enumerate(context.value_propositions, 1):
                st.sidebar.write(f"  {i}. {prop['title']}: {prop['content']}")

def main():
    """Main application function."""
    # Initialize services
    config, llm_service, prompt_builder = initialize_services()
    
    if config is None:
        st.stop()
    
    # Render configuration sidebar
    config = render_configuration_sidebar(config)
    
    # Re-initialize services if config changed
    if config.validate():
        try:
            llm_service = LLMService(config)
            prompt_builder = PromptBuilder(llm_service)
        except Exception as e:
            st.error(f"❌ Failed to reinitialize services: {e}")
            log(f"ERROR reinitializing services: {e}\n{traceback.format_exc()}", prefix="OutboundOwl")
            st.stop()
    
    # Render context display
    render_context_display(prompt_builder)
    
    # Render main chat interface
    render_chat_interface(prompt_builder)

if __name__ == "__main__":
    main() 