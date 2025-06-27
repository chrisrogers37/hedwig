import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import json

class AppConfig:
    """
    Centralized configuration service for Hedwig.
    Loads settings from environment variables, optional config file, and allows runtime updates.
    Currently supports OpenAI, with extensible structure for additional providers.
    """
    DEFAULTS = {
        "PROVIDER": "openai",  # Currently only supports "openai"
        "OPENAI_API_KEY": None,
        "OPENAI_MODEL": "gpt-4",
        "DEFAULT_TONE": "professional",
        "DEFAULT_LANGUAGE": "English",
    }

    def __init__(self, config_file: Optional[str] = None, load_env: bool = True):
        if load_env:
            load_dotenv()
        self._config: Dict[str, Any] = self.DEFAULTS.copy()
        self._load_env()
        if config_file:
            self._load_file(config_file)

    def _load_env(self):
        for key in self.DEFAULTS:
            val = os.getenv(key)
            if val is not None:
                self._config[key] = val

    def _load_file(self, config_file: str):
        try:
            with open(config_file, 'r') as f:
                if config_file.endswith('.json'):
                    data = json.load(f)
                else:
                    raise ValueError("Only JSON config files are supported.")
            for key, val in data.items():
                if key in self.DEFAULTS:
                    self._config[key] = val
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        self._config[key] = value

    @property
    def provider(self) -> str:
        return self._config["PROVIDER"]

    @property
    def openai_api_key(self) -> Optional[str]:
        return self._config["OPENAI_API_KEY"]

    @property
    def openai_model(self) -> str:
        return self._config["OPENAI_MODEL"]

    @property
    def default_tone(self) -> str:
        return self._config["DEFAULT_TONE"]

    @property
    def default_language(self) -> str:
        return self._config["DEFAULT_LANGUAGE"]

    def get_api_key(self) -> Optional[str]:
        """Get the API key for the current provider."""
        if self.provider == "openai":
            return self.openai_api_key
        # Future providers would be added here
        return None

    def get_model(self) -> str:
        """Get the model for the current provider."""
        if self.provider == "openai":
            return self.openai_model
        # Future providers would be added here
        return ""

    def validate(self) -> bool:
        """Validate required config fields. Returns True if valid, else False."""
        if self.provider == "openai":
            if not self.openai_api_key:
                print("Error: OPENAI_API_KEY is required.")
                return False
        # Future providers would be validated here
        return True

def get_config() -> AppConfig:
    config = AppConfig()
    config.validate()
    return config 