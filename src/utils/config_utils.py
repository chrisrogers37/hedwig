"""
Configuration utilities for Hedwig.

This module provides standardized configuration loading, validation, and access patterns
for environment variables, config files, and runtime configuration management.
"""

import os
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dotenv import load_dotenv

from .logging_utils import log
from .file_utils import FileUtils
from .error_utils import ErrorHandler


class ConfigUtils:
    """
    Utility class for standardized configuration operations across Hedwig.
    
    Provides consistent patterns for loading environment variables, parsing config files,
    validating configuration, and managing config values.
    """
    
    @staticmethod
    def load_environment_variables(env_file: Optional[str] = None) -> None:
        """
        Load environment variables from .env file.
        
        Args:
            env_file: Path to .env file (default: auto-detect)
        """
        try:
            if env_file:
                load_dotenv(env_file)
            else:
                load_dotenv()
            log("Environment variables loaded successfully", prefix="ConfigUtils")
        except Exception as e:
            log(f"WARNING: Failed to load environment variables: {e}", prefix="ConfigUtils")
    
    @staticmethod
    def get_env_variables(keys: List[str]) -> Dict[str, Any]:
        """
        Get environment variables for specified keys.
        
        Args:
            keys: List of environment variable keys to retrieve
            
        Returns:
            Dictionary of key-value pairs for found environment variables
        """
        env_vars = {}
        for key in keys:
            value = os.getenv(key)
            if value is not None:
                env_vars[key] = value
                log(f"Loaded env var: {key} = {ConfigUtils._mask_sensitive_value(key, value)}", prefix="ConfigUtils")
        
        return env_vars
    
    @staticmethod
    def load_config_from_file(config_file: str, supported_formats: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load configuration from a file using FileUtils and ErrorHandler.
        
        Args:
            config_file: Path to the configuration file
            supported_formats: List of supported file extensions (default: ['.json'])
            
        Returns:
            Configuration dictionary or None if loading fails
        """
        if supported_formats is None:
            supported_formats = ['.json']
        
        config_path = Path(config_file)
        
        # Validate file exists and is readable
        if not FileUtils.validate_file_exists(config_path):
            log(f"WARNING: Config file not found or not readable: {config_file}", prefix="ConfigUtils")
            return None
        
        # Check file format
        if not any(config_file.endswith(fmt) for fmt in supported_formats):
            log(f"WARNING: Unsupported config file format: {config_file}", prefix="ConfigUtils")
            return None
        
        # Read file content using FileUtils
        content = FileUtils.safe_read_file(config_path)
        if content is None:
            log(f"WARNING: Failed to read config file: {config_file}", prefix="ConfigUtils")
            return None
        
        def parse_config():
            if config_file.endswith('.json'):
                data = json.loads(content)
            else:
                raise ValueError(f"Unsupported config file format: {config_file}")
            
            log(f"Successfully parsed config file: {config_file}", prefix="ConfigUtils")
            return data
        
        return ErrorHandler.handle_config_operation(parse_config)
    
    @staticmethod
    def merge_configs(defaults: Dict[str, Any], 
                     env_vars: Dict[str, Any], 
                     file_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Merge configuration from multiple sources with priority: file > env > defaults.
        
        Args:
            defaults: Default configuration values
            env_vars: Environment variable values
            file_config: File-based configuration values (optional)
            
        Returns:
            Merged configuration dictionary
        """
        config = defaults.copy()
        
        # Apply environment variables (override defaults)
        config.update(env_vars)
        
        # Apply file config (override env and defaults)
        if file_config:
            config.update(file_config)
        
        log(f"Merged config from {len(defaults)} defaults, {len(env_vars)} env vars, {len(file_config or {})} file values", prefix="ConfigUtils")
        return config
    
    @staticmethod
    def validate_config(config: Dict[str, Any], 
                       required_keys: List[str], 
                       optional_keys: List[str] = None) -> bool:
        """
        Validate configuration against required and optional keys.
        
        Args:
            config: Configuration dictionary to validate
            required_keys: List of keys that must be present and non-empty
            optional_keys: List of keys that are optional (default: None)
            
        Returns:
            True if configuration is valid, False otherwise
        """
        if optional_keys is None:
            optional_keys = []
        
        # Check required keys
        missing_keys = []
        for key in required_keys:
            if key not in config or not config[key]:
                missing_keys.append(key)
        
        if missing_keys:
            log(f"ERROR: Missing required config keys: {missing_keys}", prefix="ConfigUtils")
            return False
        
        # Check for unknown keys (optional validation)
        all_valid_keys = set(required_keys) | set(optional_keys)
        unknown_keys = set(config.keys()) - all_valid_keys
        if unknown_keys:
            log(f"WARNING: Unknown config keys found: {unknown_keys}", prefix="ConfigUtils")
        
        log(f"Configuration validation passed: {len(required_keys)} required, {len(optional_keys)} optional", prefix="ConfigUtils")
        return True
    
    @staticmethod
    def get_nested_config(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """
        Get nested configuration value using dot notation (e.g., 'database.host').
        
        Args:
            config: Configuration dictionary
            key_path: Dot-separated path to the configuration key
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        current = config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    @staticmethod
    def set_nested_config(config: Dict[str, Any], key_path: str, value: Any) -> bool:
        """
        Set nested configuration value using dot notation (e.g., 'database.host').
        
        Args:
            config: Configuration dictionary to modify
            key_path: Dot-separated path to the configuration key
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        keys = key_path.split('.')
        current = config
        
        try:
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set the value
            current[keys[-1]] = value
            log(f"Set nested config: {key_path} = {ConfigUtils._mask_sensitive_value(key_path, value)}", prefix="ConfigUtils")
            return True
        except Exception as e:
            log(f"ERROR: Failed to set nested config {key_path}: {e}", prefix="ConfigUtils")
            return False
    
    @staticmethod
    def mask_sensitive_config(config: Dict[str, Any], 
                             sensitive_keys: List[str] = None) -> Dict[str, Any]:
        """
        Create a copy of config with sensitive values masked for logging.
        
        Args:
            config: Configuration dictionary
            sensitive_keys: List of keys to mask (default: common sensitive keys)
            
        Returns:
            Configuration dictionary with sensitive values masked
        """
        if sensitive_keys is None:
            sensitive_keys = ['api_key', 'password', 'secret', 'token']
        
        masked_config = config.copy()
        
        for key, value in masked_config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                masked_config[key] = ConfigUtils._mask_sensitive_value(key, value)
        
        return masked_config
    
    @staticmethod
    def _mask_sensitive_value(key: str, value: Any) -> str:
        """Mask sensitive values for logging."""
        if not value or not isinstance(value, str):
            return str(value)
        
        if len(value) < 8:
            return "***"
        
        # Different masking patterns based on key type
        if 'api_key' in key.lower():
            # API keys: first 4 + ... + last 4
            return value[:4] + "..." + value[-4:]
        else:
            # Passwords and other secrets: first 4 + ... + last 3
            return value[:4] + "..." + value[-3:]
    
    @staticmethod
    def export_config(config: Dict[str, Any], 
                     output_file: str, 
                     format: str = 'json') -> bool:
        """
        Export configuration to a file.
        
        Args:
            config: Configuration dictionary to export
            output_file: Path to output file
            format: Export format ('json' or 'env')
            
        Returns:
            True if export successful, False otherwise
        """
        def export_operation():
            if format == 'json':
                content = json.dumps(config, indent=2)
            elif format == 'env':
                content = '\n'.join([f"{key}={value}" for key, value in config.items()])
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            return FileUtils.safe_write_file(Path(output_file), content)
        
        success = ErrorHandler.handle_file_operation(export_operation)
        if success:
            log(f"Configuration exported to {output_file} in {format} format", prefix="ConfigUtils")
        else:
            log(f"ERROR: Failed to export configuration to {output_file}", prefix="ConfigUtils")
        
        return bool(success) 