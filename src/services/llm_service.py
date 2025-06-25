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
    
    def generate_response(self, prompt: str, max_tokens: int = 1200, temperature: float = 0.7) -> str:
        """Send the prompt to the LLM and return the response. Log all prompts and responses."""
        model = getattr(self.config, 'openai_model', 'gpt-4')
        try:
            log(f"Sending prompt to OpenAI ({model}):\n{prompt}", prefix="LLMService")
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            llm_output = response.choices[0].message.content
            log(f"OpenAI response:\n{llm_output}", prefix="LLMService")
            return llm_output
        except Exception as e:
            log(f"OpenAI API error: {e}", prefix="LLMService")
            raise 