"""
Prompt Builder Service for Hedwig

Builds intelligent prompts for the LLM by combining user context with relevant email templates.
"""

from ..utils.logging_utils import log
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from .llm_service import LLMService
from .chat_history_manager import ChatHistoryManager, MessageType
from .scroll_retriever import ScrollRetriever, EmailSnippet
from .profile_manager import ProfileManager
from ..utils.text_utils import TextProcessor

class PromptBuilder:
    """
    Handles prompt construction for email generation, using full conversation history from ChatHistoryManager.
    Now includes RAG functionality for retrieving relevant email templates.
    """
    def __init__(self, llm_service: LLMService, chat_history_manager: ChatHistoryManager, profile_manager: Optional[ProfileManager] = None, config=None, scroll_retriever: Optional[ScrollRetriever] = None):
        self.llm_service = llm_service
        self.chat_history_manager = chat_history_manager
        self.profile_manager = profile_manager or ProfileManager()
        self.config = config
        self.scroll_retriever = scroll_retriever
        self.draft_email = None
        self.last_retrieved_snippets = []
        # Cache for initial template to persist guidance across turns
        self.initial_template_cache = None
        self.conversation_started = False

    def _retrieve_relevant_snippets(self, user_context: str) -> List[Tuple[EmailSnippet, float]]:
        """
        Retrieve relevant email snippets based on user context.
        Caches the initial template to persist guidance across conversation turns.
        
        Args:
            user_context: The user's request/context for email generation
            
        Returns:
            List of (snippet, similarity_score) tuples
        """
        if not self.scroll_retriever:
            log("No scroll retriever available, skipping template retrieval", prefix="PromptBuilder")
            return []
        
        try:
            # Build enhanced context from latest user message + all feedback
            enhanced_context = self._build_enhanced_context(user_context)
            
            # Query for relevant snippets with a reasonable similarity threshold
            snippets = self.scroll_retriever.query(
                query_text=enhanced_context,
                top_k=3,
                min_similarity=0.75,  # Only use templates with good semantic match
                filters=None  # Could add filters based on user preferences
            )
            
            # Cache the initial template if this is the first retrieval
            if not self.conversation_started and snippets:
                self.initial_template_cache = snippets[0]  # Cache the best match
                self.conversation_started = True
                log(f"Cached initial template: {snippets[0][0].id} (score: {snippets[0][1]:.3f})", prefix="PromptBuilder")
            
            # If we have a cached template and current snippets don't include it, 
            # add it back to ensure guidance persistence
            if self.initial_template_cache and snippets:
                cached_template_id = self.initial_template_cache[0].id
                current_template_ids = [s[0].id for s in snippets]
                
                if cached_template_id not in current_template_ids:
                    # Add cached template back to the beginning
                    snippets.insert(0, self.initial_template_cache)
                    log(f"Restored cached template: {cached_template_id} to maintain guidance consistency", prefix="PromptBuilder")
            
            if snippets:
                log(f"Retrieved {len(snippets)} relevant templates with similarity scores: {[f'{s[1]:.3f}' for s in snippets]}", prefix="PromptBuilder")
                for snippet, score in snippets:
                    log(f"Template: {snippet.id} (score: {score:.3f}) - {snippet.use_case} for {snippet.industry}", prefix="PromptBuilder")
            else:
                log("No relevant templates found above similarity threshold (0.75). Proceeding without template references.", prefix="PromptBuilder")
            
            self.last_retrieved_snippets = snippets
            return snippets
            
        except Exception as e:
            log(f"Error retrieving snippets: {e}", prefix="PromptBuilder")
            return []

    def _build_enhanced_context(self, latest_user_message: str) -> str:
        """
        Build enhanced context by combining all user messages (initial prompt and feedback) in chronological order.
        If the latest_user_message is not already in the chat history, include it at the end.
        
        Args:
            latest_user_message: The most recent user message
        
        Returns:
            Enhanced context string for RAG retrieval
        """
        # Get all user messages (both initial prompts and feedback) in order
        user_messages = [msg.content for msg in self.chat_history_manager.messages 
                        if msg.type in (MessageType.INITIAL_PROMPT, MessageType.FEEDBACK)]
        
        # If the latest_user_message is not in the list, append it
        if not user_messages or (user_messages and user_messages[-1] != latest_user_message):
            user_messages.append(latest_user_message)
        
        enhanced_context = " ".join(user_messages)
        log(f"Enhanced RAG context: {enhanced_context[:100]}...", prefix="PromptBuilder")
        return enhanced_context

    def _build_rag_context(self, snippets: List[Tuple[EmailSnippet, float]]) -> str:
        """
        Build RAG context section for the prompt with clear instructions about template usage.
        
        Args:
            snippets: List of (snippet, similarity_score) tuples
            
        Returns:
            Formatted RAG context string
        """
        if not snippets:
            return ""
        
        rag_context = """
**REFERENCE EMAIL TEMPLATES**
The following email examples are provided for inspiration regarding tone, industry language, and formatting structure. 

⚠️  IMPORTANT: Do NOT copy specific details from these templates such as:
- Company names, products, or services
- Statistics, metrics, or performance data
- Recent news, events, or time-sensitive information
- Personal anecdotes or stories

Use these examples ONLY for:
- Industry-appropriate tone and language
- Email structure and formatting
- Approximate email length
- General approach to the type of outreach

"""
        
        for i, (snippet, score) in enumerate(snippets, 1):
            rag_context += f"""
--- Example {i} (Similarity: {score:.3f}) ---
Use Case: {snippet.use_case}
Industry: {snippet.industry}
Tone: {snippet.tone}

{snippet.content}

"""
        
        # Add guidance from retrieved templates
        guidance_parts = []
        for snippet, _ in snippets:
            if snippet.guidance:
                guidance_parts.append(self._format_guidance(snippet.guidance))
        
        if guidance_parts:
            rag_context += """
**WRITING GUIDANCE:**
Based on the selected template, follow these guidelines:

"""
            rag_context += "\n\n".join(guidance_parts)
        
        rag_context += """
**END REFERENCE TEMPLATES**

Now, write a completely original email for the user's specific situation, using the above examples only for style and structure guidance.
"""
        
        return rag_context
    
    def _format_guidance(self, guidance: Dict[str, Any]) -> str:
        """Format guidance for LLM consumption."""
        formatted = []
        
        if 'avoid_phrases' in guidance and guidance['avoid_phrases']:
            formatted.append("🚫 **AVOID THESE PHRASES:**")
            for phrase in guidance['avoid_phrases']:
                formatted.append(f"   • \"{phrase}\"")
            formatted.append("")
        
        if 'preferred_phrases' in guidance and guidance['preferred_phrases']:
            formatted.append("✅ **PREFERRED PHRASES:**")
            for phrase in guidance['preferred_phrases']:
                formatted.append(f"   • \"{phrase}\"")
            formatted.append("")
        
        if 'writing_tips' in guidance and guidance['writing_tips']:
            formatted.append("💡 **WRITING TIPS:**")
            for tip in guidance['writing_tips']:
                formatted.append(f"   • {tip}")
            formatted.append("")
        
        return "\n".join(formatted)

    def build_llm_prompt(self) -> str:
        # Get conversation context
        conversation_context = self._build_full_conversation_context()

        # Get profile context from ProfileManager
        profile_text = self.profile_manager.get_profile_context(include_sensitive=True)

        # Retrieve relevant snippets for RAG
        latest_user_message = self._get_latest_user_message()
        snippets = self._retrieve_relevant_snippets(latest_user_message)
        rag_context = self._build_rag_context(snippets)

        # Build the prompt
        prompt = f"""
You are an expert assistant for writing outreach emails for any use case.

You have been speaking to the user, the conversation history is immediately below.

{conversation_context}

User profile (if provided):
{profile_text if profile_text else '[No profile info provided]'}

{"Based on your experience and the user's need, you know that the following context is relevant to the user's request, and should use it to guide your response:" if rag_context else ""}
{rag_context}

**INSTRUCTIONS:**
1. Generate a draft outreach email for the user's goal.
2. If a template was retrieved, replace all template placeholders with appropriate values.
3. If you need more details, ask the user for what you need.
5. If this is feedback on a previous draft, incorporate the user's feedback based on the last message in the conversation history.
"""
        return prompt

    def _get_latest_user_message(self) -> str:
        """Get the latest user message (initial prompt or feedback)."""
        user_messages = [msg for msg in self.chat_history_manager.messages 
                        if msg.type in (MessageType.INITIAL_PROMPT, MessageType.FEEDBACK)]
        return user_messages[-1].content if user_messages else "[No user request provided]"

    def _build_full_conversation_context(self) -> str:
        """Build the full conversation context in chronological order."""
        if not self.chat_history_manager.messages:
            return "No conversation history available."
        
        context_parts = []
        
        for message in self.chat_history_manager.messages:
            if message.type in (MessageType.INITIAL_PROMPT, MessageType.FEEDBACK):
                context_parts.append(f"User: {message.content}")
            elif message.type in (MessageType.DRAFT, MessageType.REVISED_DRAFT):
                context_parts.append(f"Assistant: {message.content}")
            elif message.type == MessageType.SYSTEM:
                context_parts.append(f"System: {message.content}")
        
        return "\n\n".join(context_parts)

    def _build_conversation_context(self) -> str:
        """Build conversation context for the prompt (deprecated - use _build_full_conversation_context)."""
        return self._build_full_conversation_context()

    def _get_previous_draft_context(self) -> str:
        """Get the previous draft if this is a feedback scenario (deprecated)."""
        # This method is now deprecated since we use full conversation context
        return ""

    def _extract_feedback_instructions(self, user_message: str) -> str:
        """Extract specific feedback instructions from user message (deprecated)."""
        # This method is now deprecated since we use message types
        return ""

    def generate_draft(self):
        prompt = self.build_llm_prompt()
        log(f"Prompt sent to LLM:\n{prompt}", prefix="PromptBuilder")
        llm_response = self.llm_service.generate_response(prompt, max_tokens=1500)
        log(f"LLM response:\n{llm_response}", prefix="PromptBuilder")
        self.chat_history_manager.add_draft(llm_response)
        self.draft_email = llm_response
        return llm_response

    def get_draft_email(self) -> Optional[str]:
        return self.draft_email

    def update_profile(self, **kwargs):
        """Update the user profile with new information."""
        self.profile_manager.update_profile(**kwargs)
        log(f"Profile updated via ProfileManager: {kwargs}", prefix="PromptBuilder")

    def get_last_retrieved_snippets(self) -> List[Tuple[EmailSnippet, float]]:
        """Get the last retrieved snippets for debugging or UI display."""
        return self.last_retrieved_snippets
    
    def reset_conversation_cache(self):
        """Reset the template cache when starting a new conversation."""
        self.initial_template_cache = None
        self.conversation_started = False
        log("Reset template cache for new conversation", prefix="PromptBuilder") 