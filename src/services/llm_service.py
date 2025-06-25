from typing import Dict, Optional, Any, Tuple
import openai
from .config_service import AppConfig
import os
from .config_service import get_config
from .logging_utils import log


class LLMService:
    """
    Service for interacting with Large Language Models.
    Currently supports OpenAI, with extensible structure for additional providers.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self._setup_client()
    
    def _setup_client(self):
        """Setup the appropriate client based on the configured provider."""
        if self.config.provider == "openai":
            api_key = self.config.get_api_key()
            if not api_key:
                raise ValueError("OpenAI API key is required")
            # New OpenAI API (1.0.0+) uses client-based approach
            self.client = openai.OpenAI(api_key=api_key)
        # Future providers would be added here
    
    def generate_response(self, prompt: str, max_tokens: int = 1200) -> str:
        """Send the prompt to the LLM and return the response. Log all prompts and responses."""
        model = getattr(self.config, 'openai_model', 'gpt-4')
        try:
            log(f"Sending prompt to OpenAI ({model}):\n{prompt}", prefix="LLMService")
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            llm_output = response.choices[0].message.content
            log(f"OpenAI response:\n{llm_output}", prefix="LLMService")
            return llm_output
        except Exception as e:
            log(f"OpenAI API error: {e}", prefix="LLMService")
            raise
    
    def generate_email(self, context: Dict[str, Any], email_type: str = "outreach") -> str:
        """
        Generate an email based on context and type.
        
        Args:
            context: Dictionary containing email context (recipient info, value props, etc.)
            email_type: Type of email ("outreach" or "followup")
            
        Returns:
            Generated email text
        """
        prompt = self._build_email_prompt(context, email_type)
        return self.generate_response(prompt, max_tokens=1500, temperature=0.7)
    
    def _build_email_prompt(self, context: Dict[str, Any], email_type: str) -> str:
        """Build a prompt for email generation based on context and type."""
        
        # Extract context variables
        your_name = context.get("your_name", "Your Name")
        your_title = context.get("your_title", "Your Title")
        company_name = context.get("company_name", "Your Company")
        recipient_name = context.get("recipient_name", "Recipient")
        recipient_organization = context.get("recipient_organization", "Their Organization")
        
        if email_type.lower() == "outreach":
            return self._build_outreach_prompt(context, your_name, your_title, company_name, 
                                             recipient_name, recipient_organization)
        elif email_type.lower() == "followup":
            return self._build_followup_prompt(context, your_name, your_title, company_name,
                                             recipient_name, recipient_organization)
        else:
            raise ValueError(f"Unsupported email type: {email_type}")
    
    def _build_outreach_prompt(self, context: Dict[str, Any], your_name: str, your_title: str, 
                              company_name: str, recipient_name: str, recipient_organization: str) -> str:
        """Build prompt for outreach emails."""
        
        value_propositions = context.get("value_propositions", [])
        call_to_action = context.get("call_to_action", "schedule a meeting")
        additional_notes = context.get("additional_notes", "")
        
        # Build value propositions section
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
Tone: {self.config.default_tone}
Language: {self.config.default_language}

{value_props_text}

Call to Action: {call_to_action}

Additional Context: {additional_notes}

Please write a professional, personalized outreach email that:
1. Is concise and engaging
2. References the recipient's organization
3. Highlights the value propositions
4. Includes a clear call to action
5. Maintains a {self.config.default_tone} tone

Format the email with proper greeting, body, and signature."""

        return prompt
    
    def _build_followup_prompt(self, context: Dict[str, Any], your_name: str, your_title: str,
                              company_name: str, recipient_name: str, recipient_organization: str) -> str:
        """Build prompt for follow-up emails."""
        
        discussion_notes = context.get("discussion_notes", "")
        pain_points = context.get("pain_points", "")
        next_steps = context.get("next_steps", "")
        additional_notes = context.get("additional_notes", "")
        
        prompt = f"""You are a professional sales representative writing a follow-up email after a meeting or conversation.

Your Information:
- Name: {your_name}
- Title: {your_title}
- Company: {company_name}

Recipient Information:
- Name: {recipient_name}
- Organization: {recipient_organization}

Email Type: Follow-up
Tone: {self.config.default_tone}
Language: {self.config.default_language}

Discussion Notes: {discussion_notes}
Pain Points Identified: {pain_points}
Agreed Next Steps: {next_steps}
Additional Context: {additional_notes}

Please write a professional follow-up email that:
1. Thanks the recipient for their time
2. Summarizes key points from the discussion
3. References specific pain points or challenges discussed
4. Outlines agreed next steps
5. Maintains a {self.config.default_tone} tone

Format the email with proper greeting, body, and signature."""

        return prompt 