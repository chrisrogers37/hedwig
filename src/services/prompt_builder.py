from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from .llm_service import LLMService
from .logging_utils import log

@dataclass
class Profile:
    your_name: str = ""
    your_title: str = ""
    company_name: str = ""
    # Add more fields as needed

class PromptBuilder:
    """
    Handles prompt construction and draft-refine loop for email generation.
    No longer extracts JSON context from conversation; only uses optional profile info.
    """
    def __init__(self, llm_service: LLMService, profile: Optional[Profile] = None):
        self.llm_service = llm_service
        self.profile = profile or Profile()
        self.draft_email = None
        self.last_user_message = None

    def build_email_prompt(self, user_message: str, feedback: Optional[str] = None) -> str:
        profile_lines = []
        if self.profile.your_name:
            profile_lines.append(f"Name: {self.profile.your_name}")
        if self.profile.your_title:
            profile_lines.append(f"Title: {self.profile.your_title}")
        if self.profile.company_name:
            profile_lines.append(f"Company: {self.profile.company_name}")
        profile_text = "\n".join(profile_lines)
        feedback_text = f"\n\nUser feedback: {feedback}" if feedback else ""
        prompt = (
            f"""
You are an expert assistant for writing sales outreach emails.

Here is the user's message describing their outreach goal:
{user_message}

Here is the user's optional profile information (use if helpful):
{profile_text if profile_text else '[No profile info provided]'}
{feedback_text}

Your job:
- Generate a draft outreach email using the information above.
- If you need more information for a truly great, personalized email, you may ask for it conversationally, but always generate a draft with what you have.
- If the user provides feedback, refine the draft accordingly.
- Be friendly, concise, and professional by default, unless the user requests otherwise.
- Do not block draft generation for missing info. Never require all fields to be filled.
- If the user says they're ready, just output the final draft.
"""
        )
        return prompt

    def add_message(self, user_message: str, feedback: Optional[str] = None):
        self.last_user_message = user_message
        prompt = self.build_email_prompt(user_message, feedback)
        log(f"Prompt sent to LLM:\n{prompt}", prefix="PromptBuilder")
        llm_response = self.llm_service.generate_response(prompt, max_tokens=1500)
        log(f"LLM response:\n{llm_response}", prefix="PromptBuilder")
        self.draft_email = llm_response

    def get_draft_email(self) -> Optional[str]:
        return self.draft_email

    def update_profile(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self.profile, k):
                setattr(self.profile, k, v) 