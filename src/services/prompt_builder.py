from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from .llm_service import LLMService
from .logging_utils import log
from .chat_history_manager import ChatHistoryManager

@dataclass
class Profile:
    your_name: str = ""
    your_title: str = ""
    company_name: str = ""
    # Add more fields as needed

class PromptBuilder:
    """
    Handles prompt construction for email generation, using full conversation history from ChatHistoryManager.
    """
    def __init__(self, llm_service: LLMService, chat_history_manager: ChatHistoryManager, profile: Optional[Profile] = None):
        self.llm_service = llm_service
        self.chat_history_manager = chat_history_manager
        self.profile = profile or Profile()
        self.draft_email = None

    def build_llm_prompt(self) -> str:
        # Get the full conversation context (history + summary)
        conversation_context = self.chat_history_manager.get_conversation_context()
        profile_lines = []
        if self.profile.your_name:
            profile_lines.append(f"Name: {self.profile.your_name}")
        if self.profile.your_title:
            profile_lines.append(f"Title: {self.profile.your_title}")
        if self.profile.company_name:
            profile_lines.append(f"Company: {self.profile.company_name}")
        profile_text = "\n".join(profile_lines)
        prompt = (
            f"""
You are an expert assistant for writing sales outreach emails.

Conversation so far:
{conversation_context}

User profile (if provided):
{profile_text if profile_text else '[No profile info provided]'}

Your job:
- Generate or refine a draft outreach email based on the above.
- If the user provides feedback, refine the draft accordingly.
- Be friendly, concise, and professional by default, unless the user requests otherwise.
- If the user says they're ready, just output the final draft.
"""
        )
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
        for k, v in kwargs.items():
            if hasattr(self.profile, k):
                setattr(self.profile, k, v) 