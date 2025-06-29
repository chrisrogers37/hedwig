import pytest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.services.config_service import AppConfig

def test_defaults():
    # Save original values
    original_api_key = os.environ.get("OPENAI_API_KEY")
    original_model = os.environ.get("OPENAI_MODEL")
    
    # Unset for clean test
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)
    
    try:
        config = AppConfig(load_env=False)
        assert config.provider == "openai"
        assert config.openai_model == "gpt-4"
        assert config.default_tone == "professional"
        assert config.default_language == "English"
        assert config.openai_api_key is None
        assert config.get_api_key() is None
        assert config.get_model() == "gpt-4"
    finally:
        # Restore original values
        if original_api_key:
            os.environ["OPENAI_API_KEY"] = original_api_key
        if original_model:
            os.environ["OPENAI_MODEL"] = original_model

def test_env_loading(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-3.5")
    config = AppConfig(load_env=False)
    assert config.openai_api_key == "test-key"
    assert config.openai_model == "gpt-3.5"
    assert config.get_api_key() == "test-key"
    assert config.get_model() == "gpt-3.5"

def test_file_loading():
    data = {
        "PROVIDER": "openai",
        "OPENAI_API_KEY": "file-key",
        "OPENAI_MODEL": "gpt-4",
        "DEFAULT_TONE": "casual",
        "DEFAULT_LANGUAGE": "Spanish"
    }
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp:
        json.dump(data, tmp)
        tmp.flush()
        config = AppConfig(config_file=tmp.name, load_env=False)
        assert config.provider == "openai"
        assert config.openai_api_key == "file-key"
        assert config.default_tone == "casual"
        assert config.default_language == "Spanish"
        assert config.get_api_key() == "file-key"
        assert config.get_model() == "gpt-4"
    os.remove(tmp.name)

def test_set_and_get():
    config = AppConfig(load_env=False)
    config.set("OPENAI_MODEL", "gpt-3.5")
    assert config.get("OPENAI_MODEL") == "gpt-3.5"
    assert config.get_model() == "gpt-3.5"

def test_validate():
    # Save original value
    original_api_key = os.environ.get("OPENAI_API_KEY")
    
    # Unset for clean test
    os.environ.pop("OPENAI_API_KEY", None)
    
    try:
        config = AppConfig(load_env=False)
        assert not config.validate()  # No API key
        config.set("OPENAI_API_KEY", "abc")
        assert config.validate()
    finally:
        # Restore original value
        if original_api_key:
            os.environ["OPENAI_API_KEY"] = original_api_key 