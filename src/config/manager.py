import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from .settings import DEFAULT_SETTINGS, DEVELOPMENT_OVERRIDES, PRODUCTION_OVERRIDES
from ..models.config_models import AppConfig
from ..utils.errors import ConfigurationError


class ConfigManager:
    """Configuration manager using built-in json module"""
    
    def __init__(self, config_path: Optional[str] = None, environment: str = "production"):
        self.config_path = config_path or "config.json"
        self.environment = environment.lower()
        self._config_data = None
        self._app_config = None
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        if config_path:
            self.config_path = config_path
        
        try:
            # Start with default settings
            config = self._deep_copy_dict(DEFAULT_SETTINGS)
            
            # Apply environment-specific overrides
            env_overrides = self._get_environment_overrides()
            if env_overrides:
                config = self._merge_configs(config, env_overrides)
            
            # Load from file if exists
            if os.path.exists(self.config_path):
                file_config = self._load_from_file(self.config_path)
                config = self._merge_configs(config, file_config)
                print(f"Configuration loaded from {self.config_path}")
            else:
                print(f"Configuration file {self.config_path} not found, using defaults")
            
            # Validate configuration
            self.validate_config(config)
            
            self._config_data = config
            return config
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _load_from_file(self, filepath: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file {filepath}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to read config file {filepath}: {e}")
    
    def _get_environment_overrides(self) -> Optional[Dict[str, Any]]:
        """Get environment-specific configuration overrides"""
        if self.environment == "development":
            return DEVELOPMENT_OVERRIDES
        elif self.environment == "production":
            return PRODUCTION_OVERRIDES
        else:
            return None
    
    def _deep_copy_dict(self, original: Dict[str, Any]) -> Dict[str, Any]:
        """Deep copy dictionary using json serialization"""
        return json.loads(json.dumps(original))
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries recursively"""
        result = self._deep_copy_dict(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration with clear error messages"""
        try:
            # Validate required sections
            required_sections = ['scraping', 'export', 'logging']
            for section in required_sections:
                if section not in config:
                    raise ConfigurationError(f"Missing required configuration section: {section}")
            
            # Validate scraping configuration
            scraping = config['scraping']
            self._validate_scraping_config(scraping)
            
            # Validate export configuration
            export = config['export']
            self._validate_export_config(export)
            
            # Validate logging configuration
            logging = config['logging']
            self._validate_logging_config(logging)
            
            # Validate validation rules if present
            if 'validation' in config:
                self._validate_validation_config(config['validation'])
            
            return True
            
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")
    
    def _validate_scraping_config(self, scraping: Dict[str, Any]):
        """Validate scraping configuration section"""
        # Required fields
        required_fields = ['base_url', 'delay_between_requests', 'max_retries', 'timeout']
        for field in required_fields:
            if field not in scraping:
                raise ConfigurationError(f"Missing required scraping field: {field}")
        
        # Validate types and ranges
        if not isinstance(scraping['base_url'], str) or not scraping['base_url']:
            raise ConfigurationError("base_url must be a non-empty string")
        
        if not isinstance(scraping['delay_between_requests'], (int, float)) or scraping['delay_between_requests'] < 0:
            raise ConfigurationError("delay_between_requests must be a non-negative number")
        
        if not isinstance(scraping['max_retries'], int) or scraping['max_retries'] < 0:
            raise ConfigurationError("max_retries must be a non-negative integer")
        
        if not isinstance(scraping['timeout'], int) or scraping['timeout'] <= 0:
            raise ConfigurationError("timeout must be a positive integer")
        
        # Optional fields validation
        if 'headless' in scraping and not isinstance(scraping['headless'], bool):
            raise ConfigurationError("headless must be a boolean")
        
        if 'max_pages' in scraping:
            if not isinstance(scraping['max_pages'], int) or scraping['max_pages'] <= 0:
                raise ConfigurationError("max_pages must be a positive integer")
    
    def _validate_export_config(self, export: Dict[str, Any]):
        """Validate export configuration section"""
        # Required fields
        required_fields = ['output_directory', 'filename_prefix']
        for field in required_fields:
            if field not in export:
                raise ConfigurationError(f"Missing required export field: {field}")
        
        # Validate types
        if not isinstance(export['output_directory'], str) or not export['output_directory']:
            raise ConfigurationError("output_directory must be a non-empty string")
        
        if not isinstance(export['filename_prefix'], str) or not export['filename_prefix']:
            raise ConfigurationError("filename_prefix must be a non-empty string")
        
        # Optional fields
        if 'include_timestamp' in export and not isinstance(export['include_timestamp'], bool):
            raise ConfigurationError("include_timestamp must be a boolean")
    
    def _validate_logging_config(self, logging: Dict[str, Any]):
        """Validate logging configuration section"""
        # Validate log level
        if 'log_level' in logging:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if logging['log_level'] not in valid_levels:
                raise ConfigurationError(f"log_level must be one of: {valid_levels}")
        
        # Optional fields
        if 'console_output' in logging and not isinstance(logging['console_output'], bool):
            raise ConfigurationError("console_output must be a boolean")
    
    def _validate_validation_config(self, validation: Dict[str, Any]):
        """Validate validation rules configuration"""
        # Validate numeric ranges
        numeric_fields = ['min_price', 'max_price', 'max_percentage_change']
        for field in numeric_fields:
            if field in validation:
                if not isinstance(validation[field], (int, float)) or validation[field] < 0:
                    raise ConfigurationError(f"{field} must be a non-negative number")
        
        # Validate max_symbol_length
        if 'max_symbol_length' in validation:
            if not isinstance(validation['max_symbol_length'], int) or validation['max_symbol_length'] <= 0:
                raise ConfigurationError("max_symbol_length must be a positive integer")
    
    def get_app_config(self) -> AppConfig:
        """Get validated AppConfig object"""
        if not self._config_data:
            self.load_config()
        
        if not self._app_config:
            try:
                self._app_config = AppConfig(
                    scraping=self._config_data['scraping'],
                    export=self._config_data['export'],
                    logging=self._config_data['logging']
                )
            except Exception as e:
                raise ConfigurationError(f"Failed to create AppConfig: {e}")
        
        return self._app_config
    
    def save_config(self, config: Dict[str, Any], filepath: Optional[str] = None) -> str:
        """Save configuration to JSON file"""
        save_path = filepath or self.config_path
        
        try:
            # Validate before saving
            self.validate_config(config)
            
            # Ensure directory exists
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file with pretty formatting
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"Configuration saved to {save_path}")
            return save_path
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration to {save_path}: {e}")
    
    def create_default_config_file(self, filepath: Optional[str] = None) -> str:
        """Create a default configuration file"""
        save_path = filepath or self.config_path
        
        try:
            config = self._deep_copy_dict(DEFAULT_SETTINGS)
            return self.save_config(config, save_path)
        except Exception as e:
            raise ConfigurationError(f"Failed to create default config file: {e}")
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'scraping.timeout')"""
        if not self._config_data:
            self.load_config()
        
        try:
            keys = key_path.split('.')
            value = self._config_data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    def set_config_value(self, key_path: str, value: Any):
        """Set configuration value using dot notation"""
        if not self._config_data:
            self.load_config()
        
        try:
            keys = key_path.split('.')
            config = self._config_data
            
            # Navigate to the parent of the target key
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # Set the value
            config[keys[-1]] = value
            
            # Invalidate cached app config
            self._app_config = None
            
        except Exception as e:
            raise ConfigurationError(f"Failed to set config value {key_path}: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        if not self._config_data:
            self.load_config()
        
        return {
            'config_file': self.config_path,
            'config_exists': os.path.exists(self.config_path),
            'environment': self.environment,
            'sections': list(self._config_data.keys()),
            'scraping_url': self._config_data.get('scraping', {}).get('base_url'),
            'output_directory': self._config_data.get('export', {}).get('output_directory'),
            'log_level': self._config_data.get('logging', {}).get('log_level')
        }