from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from .llm_service import LLMService
from .logging_utils import log
from .chat_history_manager import ChatHistoryManager, MessageType
from .scroll_retriever import ScrollRetriever, EmailSnippet

@dataclass
class Profile:
    your_name: str = ""
    your_title: str = ""
    company_name: str = ""
    # Add more fields as needed

class PromptBuilder:
    """
    Handles prompt construction for email generation, using full conversation history from ChatHistoryManager.
    Now includes RAG functionality for retrieving relevant email templates.
    """
    def __init__(self, llm_service: LLMService, chat_history_manager: ChatHistoryManager, profile: Optional[Profile] = None, config=None, scroll_retriever: Optional[ScrollRetriever] = None):
        self.llm_service = llm_service
        self.chat_history_manager = chat_history_manager
        self.profile = profile or Profile()
        self.draft_email = None
        self.config = config or getattr(llm_service, 'config', None)
        self.scroll_retriever = scroll_retriever
        self.last_retrieved_snippets: List[Tuple[EmailSnippet, float]] = []

    def _get_tone_instructions(self, tone: str) -> str:
        tone = tone.lower()
        if tone == "professional":
            return "Use clear, concise, and formal business language. Avoid slang, contractions, or overly casual expressions. Structure the email with a logical flow, maintain a respectful and courteous tone, and focus on clarity and precision. Ensure all communication is polite, objective, and appropriate for a business audience."
        elif tone == "casual":
            return "Use simple, easy-to-understand language. Do not pontificate or explain things in grandiose ways. Embrace brevity in email construction and try to get to the point in a way that makes the email not a burden to read. Feel free to use contractions and a relaxed, conversational style."
        elif tone == "friendly":
            return "Write in a warm, approachable, and personable manner. Use positive language and show genuine interest in the recipient. Feel free to include light pleasantries or well-wishes, and make the email feel inviting and supportive. Avoid being overly formal, but maintain professionalism."
        elif tone == "formal":
            return "Use highly structured, polite, and respectful language. Avoid contractions and colloquialisms. Address the recipient with appropriate titles and maintain a clear separation between personal and professional topics. Ensure the email is grammatically precise and follows traditional business etiquette."
        elif tone == "natural":
            return "Use simple language and intentionally try to not sound AI-written. Do not use exotic words or words with flair. Do not write in the overly peppy way often associated with AI. Do not use em dashes."
        else:
            return ""

    def _retrieve_relevant_snippets(self, user_context: str) -> List[Tuple[EmailSnippet, float]]:
        """
        Retrieve relevant email snippets based on user context.
        
        Args:
            user_context: The user's request/context for email generation
            
        Returns:
            List of (snippet, similarity_score) tuples
        """
        if not self.scroll_retriever:
            log("No scroll retriever available, skipping template retrieval", prefix="PromptBuilder")
            return []
        
        try:
            # Query for relevant snippets with a reasonable similarity threshold
            snippets = self.scroll_retriever.query(
                query_text=user_context,
                top_k=3,
                min_similarity=0.4,  # Only use templates with good semantic match
                filters=None  # Could add filters based on user preferences
            )
            
            if snippets:
                log(f"Retrieved {len(snippets)} relevant templates with similarity scores: {[f'{s[1]:.3f}' for s in snippets]}", prefix="PromptBuilder")
                for snippet, score in snippets:
                    log(f"Template: {snippet.id} (score: {score:.3f}) - {snippet.use_case} for {snippet.industry}", prefix="PromptBuilder")
            else:
                log("No relevant templates found above similarity threshold (0.4). Proceeding without template references.", prefix="PromptBuilder")
            
            self.last_retrieved_snippets = snippets
            return snippets
            
        except Exception as e:
            log(f"Error retrieving snippets: {e}", prefix="PromptBuilder")
            return []

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
- Specific pain points or challenges
- Personal anecdotes or stories

Use these examples ONLY for:
- Industry-appropriate tone and language
- Email structure and formatting
- Professional communication style
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
        
        rag_context += """
**END REFERENCE TEMPLATES**

Now, write a completely original email for the user's specific situation, using the above examples only for style and structure guidance.
"""
        
        return rag_context

    def build_outreach_prompt(self, context: Dict[str, Any]) -> str:
        your_name = context.get("your_name", "Your Name")
        your_title = context.get("your_title", "Your Title")
        company_name = context.get("company_name", "Your Company")
        recipient_name = context.get("recipient_name", "Recipient")
        recipient_organization = context.get("recipient_organization", "Their Organization")
        value_propositions = context.get("value_propositions", [])
        call_to_action = context.get("call_to_action", "schedule a meeting")
        additional_notes = context.get("additional_notes", "")
        tone = context.get("tone") or (self.config.default_tone if self.config else "professional")
        language = context.get("language") or (self.config.default_language if self.config else "English")
        tone_instructions = self._get_tone_instructions(tone)

        value_props_text = ""
        if value_propositions:
            value_props_text = "\n\nKey Value Propositions:\n"
            for i, prop in enumerate(value_propositions, 1):
                if prop.get("title") and prop.get("content"):
                    value_props_text += f"{i}. {prop['title']}: {prop['content']}\n"

        prompt = f"""You are a professional sales representative writing a personalized outreach email.

Your Information:
- Name: {your_name}
- Title: {your_title}
- Company: {company_name}

Recipient Information:
- Name: {recipient_name}
- Organization: {recipient_organization}

Email Type: Initial Outreach
Tone: {tone}
{tone_instructions}
Language: {language}

{value_props_text}

Call to Action: {call_to_action}

Additional Context: {additional_notes}

Please write a professional, personalized outreach email that:
1. Is concise and engaging
2. References the recipient's organization
3. Highlights the value propositions
4. Includes a clear call to action
5. Maintains a {tone} tone

Format the email with proper greeting, body, and signature."""
        return prompt

    def build_followup_prompt(self, context: Dict[str, Any]) -> str:
        your_name = context.get("your_name", "Your Name")
        your_title = context.get("your_title", "Your Title")
        company_name = context.get("company_name", "Your Company")
        recipient_name = context.get("recipient_name", "Recipient")
        recipient_organization = context.get("recipient_organization", "Their Organization")
        discussion_notes = context.get("discussion_notes", "")
        pain_points = context.get("pain_points", "")
        next_steps = context.get("next_steps", "")
        additional_notes = context.get("additional_notes", "")
        tone = context.get("tone") or (self.config.default_tone if self.config else "professional")
        language = context.get("language") or (self.config.default_language if self.config else "English")
        tone_instructions = self._get_tone_instructions(tone)

        prompt = f"""You are a professional sales representative writing a follow-up email after a meeting or conversation.

Your Information:
- Name: {your_name}
- Title: {your_title}
- Company: {company_name}

Recipient Information:
- Name: {recipient_name}
- Organization: {recipient_organization}

Email Type: Follow-up
Tone: {tone}
{tone_instructions}
Language: {language}

Discussion Notes: {discussion_notes}
Pain Points Identified: {pain_points}
Agreed Next Steps: {next_steps}
Additional Context: {additional_notes}

Please write a professional follow-up email that:
1. Thanks the recipient for their time
2. Summarizes key points from the discussion
3. References specific pain points or challenges discussed
4. Outlines agreed next steps
5. Maintains a {tone} tone

Format the email with proper greeting, body, and signature."""
        return prompt

    def build_llm_prompt(self) -> str:
        # Extract the latest user message as the main goal/request
        user_messages = [msg for msg in self.chat_history_manager.messages if msg.type in (MessageType.INITIAL_PROMPT, MessageType.FEEDBACK)]
        latest_user_message = user_messages[-1].content if user_messages else "[No user request provided]"

        # Optionally include the latest feedback
        latest_feedback = None
        feedbacks = [msg for msg in self.chat_history_manager.messages if msg.type == MessageType.FEEDBACK]
        if feedbacks:
            latest_feedback = feedbacks[-1].content

        # Profile info
        profile_lines = []
        if self.profile.your_name:
            profile_lines.append(f"Name: {self.profile.your_name}")
        if self.profile.your_title:
            profile_lines.append(f"Title: {self.profile.your_title}")
        if self.profile.company_name:
            profile_lines.append(f"Company: {self.profile.company_name}")
        profile_text = "\n".join(profile_lines)

        # Tone and language
        tone = getattr(self.config, 'default_tone', 'natural') if self.config else 'natural'
        language = getattr(self.config, 'default_language', 'English') if self.config else 'English'
        tone_instructions = self._get_tone_instructions(tone)

        # Retrieve relevant snippets for RAG
        snippets = self._retrieve_relevant_snippets(latest_user_message)
        rag_context = self._build_rag_context(snippets)

        # Build the prompt
        prompt = f"""
You are an expert assistant for writing outreach emails for any use case.

User's main goal/request:
{latest_user_message}
"""
        if latest_feedback:
            prompt += f"\nMost recent feedback from user:\n{latest_feedback}\n"
        prompt += f"""

User profile (if provided):
{profile_text if profile_text else '[No profile info provided]'}

Settings:
- Tone: {tone}
{tone_instructions}
- Language: {language}

{rag_context}

Instructions:
- If you have enough information, generate a draft outreach email for the user's goal above.
- If you need more details, ask the user for what you need.
- Be natural and avoid sounding AI-written if 'natural' tone is selected.
- Use the reference templates above ONLY for style and structure guidance.
- Write a completely original email tailored to the user's specific situation.
"""
        return prompt

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
        for key, value in kwargs.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)
        log(f"Profile updated: {kwargs}", prefix="PromptBuilder")

    def get_last_retrieved_snippets(self) -> List[Tuple[EmailSnippet, float]]:
        """Get the last retrieved snippets for debugging or UI display."""
        return self.last_retrieved_snippets 