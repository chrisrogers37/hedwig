"""
Tests for ConfigUtils utility class.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.utils.config_utils import ConfigUtils


class TestConfigUtils:
    """Test cases for ConfigUtils utility class."""
    
    def test_load_environment_variables_success(self):
        """Test successful environment variable loading."""
        with patch('src.utils.config_utils.load_dotenv') as mock_load_dotenv:
            ConfigUtils.load_environment_variables()
            mock_load_dotenv.assert_called_once()
    
    def test_load_environment_variables_with_file(self):
        """Test environment variable loading with specific file."""
        with patch('src.utils.config_utils.load_dotenv') as mock_load_dotenv:
            ConfigUtils.load_environment_variables("test.env")
            mock_load_dotenv.assert_called_once_with("test.env")
    
    def test_load_environment_variables_failure(self):
        """Test environment variable loading failure."""
        with patch('src.utils.config_utils.load_dotenv', side_effect=Exception("Load failed")):
            # Should not raise exception, just log warning
            ConfigUtils.load_environment_variables()
    
    def test_get_env_variables_success(self):
        """Test getting environment variables successfully."""
        with patch.dict(os.environ, {'TEST_KEY': 'test_value', 'ANOTHER_KEY': 'another_value'}):
            result = ConfigUtils.get_env_variables(['TEST_KEY', 'ANOTHER_KEY', 'MISSING_KEY'])
            
            assert result['TEST_KEY'] == 'test_value'
            assert result['ANOTHER_KEY'] == 'another_value'
            assert 'MISSING_KEY' not in result
            assert len(result) == 2
    
    def test_get_env_variables_empty(self):
        """Test getting environment variables when none exist."""
        with patch.dict(os.environ, {}, clear=True):
            result = ConfigUtils.get_env_variables(['TEST_KEY', 'ANOTHER_KEY'])
            assert result == {}
    
    def test_load_config_from_file_json_success(self):
        """Test loading JSON config file successfully."""
        config_data = {"key1": "value1", "key2": "value2"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            result = ConfigUtils.load_config_from_file(config_file)
            assert result == config_data
        finally:
            os.unlink(config_file)
    
    def test_load_config_from_file_not_found(self):
        """Test loading config file that doesn't exist."""
        result = ConfigUtils.load_config_from_file("nonexistent.json")
        assert result is None
    
    def test_load_config_from_file_unsupported_format(self):
        """Test loading config file with unsupported format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some content")
            config_file = f.name
        
        try:
            result = ConfigUtils.load_config_from_file(config_file)
            assert result is None
        finally:
            os.unlink(config_file)
    
    def test_load_config_from_file_invalid_json(self):
        """Test loading config file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')
            config_file = f.name
        
        try:
            result = ConfigUtils.load_config_from_file(config_file)
            assert result is None
        finally:
            os.unlink(config_file)
    
    def test_load_config_from_file_custom_formats(self):
        """Test loading config file with custom supported formats."""
        config_data = {"key1": "value1"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            result = ConfigUtils.load_config_from_file(config_file, supported_formats=['.json', '.yaml'])
            assert result == config_data
        finally:
            os.unlink(config_file)
    
    def test_merge_configs_defaults_only(self):
        """Test merging configs with defaults only."""
        defaults = {"key1": "default1", "key2": "default2"}
        result = ConfigUtils.merge_configs(defaults, {}, None)
        assert result == defaults
    
    def test_merge_configs_env_override(self):
        """Test merging configs with environment variables overriding defaults."""
        defaults = {"key1": "default1", "key2": "default2"}
        env_vars = {"key1": "env1"}
        result = ConfigUtils.merge_configs(defaults, env_vars, None)
        assert result["key1"] == "env1"
        assert result["key2"] == "default2"
    
    def test_merge_configs_file_override(self):
        """Test merging configs with file config overriding env and defaults."""
        defaults = {"key1": "default1", "key2": "default2"}
        env_vars = {"key1": "env1"}
        file_config = {"key1": "file1", "key3": "file3"}
        result = ConfigUtils.merge_configs(defaults, env_vars, file_config)
        assert result["key1"] == "file1"  # File overrides env
        assert result["key2"] == "default2"  # Default preserved
        assert result["key3"] == "file3"  # New key from file
    
    def test_validate_config_success(self):
        """Test successful config validation."""
        config = {"required1": "value1", "required2": "value2", "optional1": "value3"}
        required_keys = ["required1", "required2"]
        optional_keys = ["optional1"]
        
        result = ConfigUtils.validate_config(config, required_keys, optional_keys)
        assert result is True
    
    def test_validate_config_missing_required(self):
        """Test config validation with missing required keys."""
        config = {"required1": "value1"}  # Missing required2
        required_keys = ["required1", "required2"]
        
        result = ConfigUtils.validate_config(config, required_keys)
        assert result is False
    
    def test_validate_config_empty_required(self):
        """Test config validation with empty required key."""
        config = {"required1": "", "required2": "value2"}  # Empty required1
        required_keys = ["required1", "required2"]
        
        result = ConfigUtils.validate_config(config, required_keys)
        assert result is False
    
    def test_validate_config_unknown_keys(self):
        """Test config validation with unknown keys (should warn but pass)."""
        config = {"required1": "value1", "unknown1": "value2"}
        required_keys = ["required1"]
        
        result = ConfigUtils.validate_config(config, required_keys)
        assert result is True  # Should pass but log warning
    
    def test_get_nested_config_success(self):
        """Test getting nested config value successfully."""
        config = {"database": {"host": "localhost", "port": 5432}}
        result = ConfigUtils.get_nested_config(config, "database.host")
        assert result == "localhost"
    
    def test_get_nested_config_deep_nesting(self):
        """Test getting deeply nested config value."""
        config = {"a": {"b": {"c": {"d": "value"}}}}
        result = ConfigUtils.get_nested_config(config, "a.b.c.d")
        assert result == "value"
    
    def test_get_nested_config_not_found(self):
        """Test getting nested config value that doesn't exist."""
        config = {"database": {"host": "localhost"}}
        result = ConfigUtils.get_nested_config(config, "database.port", default=5432)
        assert result == 5432
    
    def test_get_nested_config_invalid_path(self):
        """Test getting nested config with invalid path."""
        config = {"database": {"host": "localhost"}}
        result = ConfigUtils.get_nested_config(config, "database.host.port")
        assert result is None
    
    def test_set_nested_config_success(self):
        """Test setting nested config value successfully."""
        config = {"database": {"host": "localhost"}}
        success = ConfigUtils.set_nested_config(config, "database.port", 5432)
        assert success is True
        assert config["database"]["port"] == 5432
    
    def test_set_nested_config_create_path(self):
        """Test setting nested config value and creating path."""
        config = {}
        success = ConfigUtils.set_nested_config(config, "database.host", "localhost")
        assert success is True
        assert config["database"]["host"] == "localhost"
    
    def test_set_nested_config_failure(self):
        """Test setting nested config value failure."""
        config = {"database": "not_a_dict"}
        success = ConfigUtils.set_nested_config(config, "database.host", "localhost")
        assert success is False
    
    def test_mask_sensitive_config_default_keys(self):
        """Test masking sensitive config with default sensitive keys."""
        config = {
            "api_key": "sk-1234567890abcdef",
            "password": "secret123",
            "normal_key": "normal_value"
        }
        masked = ConfigUtils.mask_sensitive_config(config)
        
        assert masked["api_key"] == "sk-1...cdef"
        assert masked["password"] == "secr...123"
        assert masked["normal_key"] == "normal_value"
    
    def test_mask_sensitive_config_custom_keys(self):
        """Test masking sensitive config with custom sensitive keys."""
        config = {
            "custom_secret": "secret123",
            "normal_key": "normal_value"
        }
        masked = ConfigUtils.mask_sensitive_config(config, sensitive_keys=["custom_secret"])
        
        assert masked["custom_secret"] == "secr...123"
        assert masked["normal_key"] == "normal_value"
    
    def test_mask_sensitive_config_short_value(self):
        """Test masking sensitive config with short values."""
        config = {"api_key": "short"}
        masked = ConfigUtils.mask_sensitive_config(config)
        assert masked["api_key"] == "***"
    
    def test_mask_sensitive_config_non_string(self):
        """Test masking sensitive config with non-string values."""
        config = {"api_key": 12345}
        masked = ConfigUtils.mask_sensitive_config(config)
        assert masked["api_key"] == "12345"
    
    def test_export_config_json_success(self):
        """Test exporting config to JSON file successfully."""
        config = {"key1": "value1", "key2": "value2"}
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            success = ConfigUtils.export_config(config, output_file, 'json')
            assert success is True
            
            # Verify file was created with correct content
            with open(output_file, 'r') as f:
                exported = json.load(f)
            assert exported == config
        finally:
            os.unlink(output_file)
    
    def test_export_config_env_success(self):
        """Test exporting config to ENV file successfully."""
        config = {"key1": "value1", "key2": "value2"}
        
        with tempfile.NamedTemporaryFile(suffix='.env', delete=False) as f:
            output_file = f.name
        
        try:
            success = ConfigUtils.export_config(config, output_file, 'env')
            assert success is True
            
            # Verify file was created with correct content
            with open(output_file, 'r') as f:
                content = f.read()
            assert "key1=value1" in content
            assert "key2=value2" in content
        finally:
            os.unlink(output_file)
    
    def test_export_config_unsupported_format(self):
        """Test exporting config with unsupported format."""
        config = {"key1": "value1"}
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            output_file = f.name
        
        try:
            success = ConfigUtils.export_config(config, output_file, 'xml')
            assert success is False
        finally:
            os.unlink(output_file)
    
    def test_export_config_write_failure(self):
        """Test exporting config when file write fails."""
        config = {"key1": "value1"}
        
        # Try to write to a location that should fail (root directory)
        output_file = "/config.json"
        
        success = ConfigUtils.export_config(config, output_file, 'json')
        assert success is False 