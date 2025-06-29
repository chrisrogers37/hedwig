import streamlit as st
import os
from pathlib import Path
import sys
import traceback

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.services.config_service import AppConfig
from src.services.llm_service import LLMService
from src.services.prompt_builder import PromptBuilder, Profile
from src.services.chat_history_manager import ChatHistoryManager, MessageType
from src.services.scroll_retriever import ScrollRetriever
from src.utils.logging_utils import log
import pyperclip

def mask_key(key):
    if not key or len(key) < 8:
        return "***"
    return key[:4] + "..." + key[-4:]

# Page configuration
st.set_page_config(
    page_title="Hedwig - AI Email Assistant",
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
        return None, None, None, None, None
    try:
        llm_service = LLMService(config)
        chat_history_manager = ChatHistoryManager()
        chat_history_manager.start_conversation()
        scroll_retriever = ScrollRetriever()
        prompt_builder = PromptBuilder(llm_service, chat_history_manager, scroll_retriever=scroll_retriever)
        return config, llm_service, chat_history_manager, prompt_builder, scroll_retriever
    except Exception as e:
        st.error(f"❌ Failed to initialize services: {e}")
        log(f"ERROR initializing services: {e}\n{traceback.format_exc()}")
        return None, None, None, None, None

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
        ["natural", "professional", "casual", "friendly", "formal"],
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

def classify_user_message(user_input: str, chat_history_manager: ChatHistoryManager) -> MessageType:
    """
    Intelligently classify user input as either a new request or feedback.
    
    Args:
        user_input: The user's message
        chat_history_manager: The chat history manager to check context
        
    Returns:
        MessageType.INITIAL_PROMPT or MessageType.FEEDBACK
    """
    # Check if there's a recent draft to provide feedback on
    latest_draft = chat_history_manager.get_latest_draft()
    
    # Keywords that indicate feedback rather than new requests
    feedback_keywords = [
        'do not', 'don\'t', 'avoid', 'remove', 'change', 'modify', 'edit',
        'sounds', 'sounding', 'fake', 'ai-written', 'flair', 'natural',
        'tone', 'style', 'language', 'word', 'phrase', 'sentence',
        'too', 'very', 'extremely', 'overly', 'instead', 'rather',
        'make it', 'rewrite', 'rephrase', 'adjust', 'tweak'
    ]
    
    # Check if user input contains feedback indicators
    input_lower = user_input.lower()
    has_feedback_keywords = any(keyword in input_lower for keyword in feedback_keywords)
    
    # If there's a recent draft and the input looks like feedback, classify as feedback
    if latest_draft and has_feedback_keywords:
        return MessageType.FEEDBACK
    
    # If there's no recent draft, it's likely a new request
    if not latest_draft:
        return MessageType.INITIAL_PROMPT
    
    # If there's a draft but no clear feedback indicators, ask for clarification
    # For now, default to feedback if there's a recent draft
    return MessageType.FEEDBACK

def render_chat_interface(chat_history_manager, prompt_builder):
    """Render the main chat interface."""
    st.title("Hedwig: Generate Outreach Emails For Any Use Case")
    st.markdown("Chat with me to create personalized outreach emails! Just describe your goal and I'll generate a draft.")

    # Get services from session state (they should already be there from main())
    chat_history_manager = st.session_state.get('chat_history_manager', chat_history_manager)
    prompt_builder = st.session_state.get('prompt_builder', prompt_builder)

    # Add a default assistant message at initialization if history is empty
    if not chat_history_manager.messages:
        default_msg = (
            "Hi! I'm Hedwig, your AI email assistant. What kind of outreach email would you like to create today? "
            "Just describe your goal, and I'll help you draft the perfect message."
        )
        chat_history_manager.add_draft(default_msg)

    # Display chat messages from ChatHistoryManager
    messages = chat_history_manager.get_recent_messages(count=50)  # Show last 50 messages
    for message in messages:
        if message.type.value in ['draft', 'revised_draft']:
            st.chat_message("assistant").write(message.content)
        elif message.type.value == 'feedback':
            st.chat_message("user").write(f"Feedback: {message.content}")
        elif message.type.value == 'initial_prompt':
            st.chat_message("user").write(message.content)

    regenerate = st.session_state.get('regenerate', False)
    user_input = st.chat_input("Describe your outreach goal or give feedback on the draft...")

    # Only add a new message if user_input is present
    if user_input:
        log(f"User message: {user_input}", prefix="Hedwig")
        
        # Intelligently classify the message type
        message_type = classify_user_message(user_input, chat_history_manager)
        log(f"Classified message as: {message_type.value}", prefix="Hedwig")
        
        chat_history_manager.add_message(user_input, message_type)
        with st.chat_message("user"):
            if message_type == MessageType.FEEDBACK:
                st.markdown(f"Feedback: {user_input}")
            else:
                st.markdown(user_input)
        st.session_state['regenerate'] = False  # Not a regeneration, it's a new message
        regenerate = False

    # Regenerate or new user input triggers LLM call
    if regenerate or user_input:
        try:
            # Always build the prompt after the user message is added to history
            prompt = prompt_builder.build_llm_prompt()
            draft = prompt_builder.llm_service.generate_response(prompt, max_tokens=1500)
            if draft:
                chat_history_manager.add_draft(draft)  # Persist assistant reply
                st.chat_message('assistant').write(draft)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📋 Copy to Clipboard", key="copy_btn"):
                        try:
                            pyperclip.copy(draft)
                            st.success("✅ Email copied to clipboard!")
                        except Exception as e:
                            st.error(f"❌ Failed to copy: {e}")
                            log(f"ERROR copying to clipboard: {e}", prefix="Hedwig")
                with col2:
                    if st.button("🔄 Regenerate", key="regenerate_btn"):
                        st.session_state['regenerate'] = True
                        st.rerun()
            else:
                st.chat_message('assistant').write("I'm not sure how to respond. Please try again.")
        except Exception as e:
            st.error(f"❌ Error generating draft: {e}")
            log(f"ERROR generating draft: {e}", prefix="Hedwig")
        st.session_state['regenerate'] = False

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
                log(f"ERROR copying to clipboard: {e}", prefix="Hedwig")
    
    with col2:
        if st.button("🔄 Regenerate"):
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Conversation"):
            st.session_state['chat_history_manager'].clear_conversation()
            st.rerun()
    
    # Show email in expandable section
    with st.expander("📄 View Full Email"):
        st.text_area("Generated Email", email_content, height=400)

def render_conversation_stats(chat_history_manager):
    """Display conversation statistics and context."""
    if st.sidebar.checkbox("🔍 Show Conversation Stats"):
        st.sidebar.subheader("Conversation Stats")
        stats = chat_history_manager.get_conversation_stats()
        
        st.sidebar.write(f"**Total Messages:** {stats['total_messages']}")
        st.sidebar.write(f"**Drafts:** {stats['drafts']}")
        st.sidebar.write(f"**Revised Drafts:** {stats['revised_drafts']}")
        st.sidebar.write(f"**Feedback Points:** {stats['feedback']}")
        st.sidebar.write(f"**Has Summary:** {'Yes' if stats['has_summary'] else 'No'}")
        
        if stats.get('duration_minutes'):
            st.sidebar.write(f"**Duration:** {stats['duration_minutes']:.1f} minutes")
        
        # Show conversation summary if available
        if chat_history_manager.summary:
            st.sidebar.subheader("Conversation Summary")
            st.sidebar.write(chat_history_manager.summary)

def main():
    """Main application function."""
    # Initialize services
    config, llm_service, chat_history_manager, prompt_builder, scroll_retriever = initialize_services()
    
    if config is None:
        st.stop()
    
    # Render configuration sidebar
    config = render_configuration_sidebar(config)
    
    # Re-initialize services if config changed
    if config.validate():
        try:
            llm_service = LLMService(config)
            
            # Only create new instances if they don't exist in session state
            if "chat_history_manager" not in st.session_state:
                chat_history_manager = ChatHistoryManager()
                chat_history_manager.start_conversation()
                st.session_state['chat_history_manager'] = chat_history_manager
            else:
                chat_history_manager = st.session_state['chat_history_manager']
            
            if "prompt_builder" not in st.session_state:
                prompt_builder = PromptBuilder(llm_service, chat_history_manager, scroll_retriever=scroll_retriever)
                st.session_state['prompt_builder'] = prompt_builder
            else:
                prompt_builder = st.session_state['prompt_builder']
                # Update the LLM service in case it changed
                prompt_builder.llm_service = llm_service
                
        except Exception as e:
            st.error(f"❌ Failed to reinitialize services: {e}")
            log(f"ERROR reinitializing services: {e}\n{traceback.format_exc()}", prefix="Hedwig")
            st.stop()
    
    # Render conversation stats
    render_conversation_stats(chat_history_manager)
    
    # Render main chat interface
    render_chat_interface(chat_history_manager, prompt_builder)

if __name__ == "__main__":
    main() 