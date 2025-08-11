"""
Configuration Management for Facebook Marketplace Automation

Handles environment variables, configuration files, and default settings.
"""

import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Settings:
    """Configuration manager for the Facebook Marketplace automation."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize settings by loading from environment and config files."""
        # Load environment variables from .env file
        load_dotenv()
        
        # Load JSON configuration if provided
        self.config_data = {}
        if config_file and os.path.exists(config_file):
            self._load_json_config(config_file)
        elif os.path.exists('config.json'):
            self._load_json_config('config.json')
        
        # Set default values
        self._set_defaults()
    
    def _load_json_config(self, config_file: str):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            self.config_data = {}
    
    def _set_defaults(self):
        """Set default configuration values."""
        self.defaults = {
            # Facebook credentials (removed demo credentials to prevent validation bugs)
            'FACEBOOK_EMAIL': '',
            'FACEBOOK_PASSWORD': '',
            
            # Marketplace search settings
            'SEARCH_LOCATION': 'Stockholm, Sweden',
            'SEARCH_KEYWORDS': 'iphone 13,iPhone 13 Pro,iPhone 13 Pro Max,iPhone 13 Mini',
            'PRICE_RANGE_MIN': '0',
            'PRICE_RANGE_MAX': '10000',
            
            # Database settings
            'DATABASE_PATH': './data/marketplace.db',
            
            # Scheduler settings
            'SCRAPE_INTERVAL_MINUTES': '15',
            'DATA_RETENTION_HOURS': '48',
            
            # Web dashboard settings
            'FLASK_HOST': '127.0.0.1',
            'FLASK_PORT': '5000',
            'FLASK_DEBUG': 'True',
            
            # Chrome browser settings
            'CHROME_HEADLESS': 'True',
            'CHROME_WINDOW_SIZE': '1920,1080',
            'PAGE_LOAD_TIMEOUT': '30',
            'ELEMENT_TIMEOUT': '10',
            
            # Scraping settings
            'MAX_LISTINGS_PER_SEARCH': '100',
            'REQUEST_DELAY_MIN': '2',
            'REQUEST_DELAY_MAX': '5',
        }
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Get configuration value by key.
        
        Priority order:
        1. Environment variables
        2. JSON config file
        3. Default values
        4. Provided default
        """
        # Check environment variables first
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value
        
        # Check JSON config
        if key in self.config_data:
            return str(self.config_data[key])
        
        # Check nested JSON config (for compatibility)
        if key == 'FACEBOOK_EMAIL' and 'facebook_credentials' in self.config_data:
            return self.config_data['facebook_credentials'].get('email', '')
        
        if key == 'FACEBOOK_PASSWORD' and 'facebook_credentials' in self.config_data:
            return self.config_data['facebook_credentials'].get('password', '')
        
        if key == 'SEARCH_LOCATION' and 'default_location' in self.config_data:
            return self.config_data['default_location']
        
        # Check defaults
        if key in self.defaults:
            return self.defaults[key]
        
        # Return provided default
        return default or ''
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get configuration value as integer."""
        try:
            return int(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get configuration value as boolean."""
        value = self.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on', 'enabled')
    
    def get_list(self, key: str, delimiter: str = ',', default: Optional[list] = None) -> list:
        """Get configuration value as list."""
        value = self.get(key)
        if not value:
            return default or []
        return [item.strip() for item in value.split(delimiter) if item.strip()]
    
    def get_facebook_credentials(self) -> Dict[str, str]:
        """Get Facebook login credentials."""
        return {
            'email': self.get('FACEBOOK_EMAIL'),
            'password': self.get('FACEBOOK_PASSWORD')
        }
    
    def get_search_config(self) -> Dict[str, Any]:
        """Get marketplace search configuration."""
        return {
            'location': self.get('SEARCH_LOCATION'),
            'keywords': self.get_list('SEARCH_KEYWORDS'),
            'price_min': self.get_int('PRICE_RANGE_MIN'),
            'price_max': self.get_int('PRICE_RANGE_MAX'),
            'max_listings': self.get_int('MAX_LISTINGS_PER_SEARCH', 100)
        }
    
    def get_chrome_options(self) -> Dict[str, Any]:
        """Get Chrome browser configuration."""
        return {
            'headless': self.get_bool('CHROME_HEADLESS', True),
            'window_size': self.get('CHROME_WINDOW_SIZE', '1920,1080'),
            'page_load_timeout': self.get_int('PAGE_LOAD_TIMEOUT', 30),
            'element_timeout': self.get_int('ELEMENT_TIMEOUT', 10)
        }
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration."""
        return {
            'path': self.get('DATABASE_PATH'),
            'retention_hours': self.get_int('DATA_RETENTION_HOURS', 48)
        }
    
    def get_scheduler_config(self) -> Dict[str, int]:
        """Get scheduler configuration."""
        return {
            'interval_minutes': self.get_int('SCRAPE_INTERVAL_MINUTES', 15),
            'request_delay_min': self.get_int('REQUEST_DELAY_MIN', 2),
            'request_delay_max': self.get_int('REQUEST_DELAY_MAX', 5)
        }
    
    def get_flask_config(self) -> Dict[str, Any]:
        """Get Flask web application configuration."""
        return {
            'host': self.get('FLASK_HOST', '127.0.0.1'),
            'port': self.get_int('FLASK_PORT', 5000),
            'debug': self.get_bool('FLASK_DEBUG', False)
        }
    
    def validate_configuration(self) -> Dict[str, list]:
        """Validate configuration and return any issues."""
        issues = {
            'errors': [],
            'warnings': []
        }
        
        # Check required Facebook credentials
        if not self.get('FACEBOOK_EMAIL'):
            issues['errors'].append('FACEBOOK_EMAIL must be set to a valid email')
        
        if not self.get('FACEBOOK_PASSWORD'):
            issues['errors'].append('FACEBOOK_PASSWORD must be set')
        
        # Check search configuration
        if not self.get('SEARCH_LOCATION'):
            issues['warnings'].append('SEARCH_LOCATION not set, using default')
        
        if not self.get_list('SEARCH_KEYWORDS'):
            issues['warnings'].append('SEARCH_KEYWORDS not set, using default')
        
        # Check database path
        db_path = self.get('DATABASE_PATH')
        if db_path:
            db_dir = os.path.dirname(os.path.abspath(db_path))
            if not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except OSError:
                    issues['errors'].append(f'Cannot create database directory: {db_dir}')
        
        return issues
    
    def print_configuration(self):
        """Print current configuration (excluding sensitive data)."""
        print("\n=== Current Configuration ===")
        
        # Safe keys to display
        safe_keys = [
            'SEARCH_LOCATION', 'SEARCH_KEYWORDS', 'PRICE_RANGE_MIN', 'PRICE_RANGE_MAX',
            'SCRAPE_INTERVAL_MINUTES', 'DATA_RETENTION_HOURS',
            'FLASK_HOST', 'FLASK_PORT', 'FLASK_DEBUG',
            'CHROME_HEADLESS', 'CHROME_WINDOW_SIZE', 'PAGE_LOAD_TIMEOUT'
        ]
        
        for key in safe_keys:
            value = self.get(key)
            print(f"{key}: {value}")
        
        # Show Facebook email (but not password)
        email = self.get('FACEBOOK_EMAIL')
        if email:
            print(f"FACEBOOK_EMAIL: {email}")
        
        print("=" * 30)


# Global settings instance
settings = Settings()
