import os
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import json

from ..utils.logging_utils import log
from ..utils.file_utils import FileUtils
from ..utils.error_utils import ErrorHandler
from ..utils.config_utils import ConfigUtils

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
    }

    def __init__(self, config_file: Optional[str] = None, load_env: bool = True):
        # Load environment variables using ConfigUtils
        if load_env:
            ConfigUtils.load_environment_variables()
        
        # Get environment variables for our config keys
        env_vars = ConfigUtils.get_env_variables(list(self.DEFAULTS.keys()))
        
        # Load file config if provided
        file_config = None
        if config_file:
            file_config = ConfigUtils.load_config_from_file(config_file)
        
        # Merge all config sources using ConfigUtils
        self._config = ConfigUtils.merge_configs(self.DEFAULTS, env_vars, file_config)

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
        """Validate required config fields using ConfigUtils."""
        required_keys = []
        if self.provider == "openai":
            required_keys = ["OPENAI_API_KEY"]
        # Future providers would add their required keys here
        
        return ConfigUtils.validate_config(self._config, required_keys)

def get_config() -> AppConfig:
    config = AppConfig()
    config.validate()
    return config 