"""
Smart Investment Bot - Configuration Manager
Handles configuration loading and environment variables
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """
    Configuration manager for the Smart Investment Bot
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file and environment variables"""
        # Load from YAML file
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file) or {}
        else:
            print(f"Config file {self.config_path} not found, using defaults")
            self._config = self._get_default_config()
        
        # Override with environment variables
        self._override_with_env_vars()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'trading': {
                'daily_profit_target': 0.01,
                'max_daily_loss': 0.02,
                'initial_capital': 10000,
                'position_size_percent': 0.1
            },
            'risk': {
                'stop_loss_percent': 0.02,
                'take_profit_percent': 0.03,
                'max_positions': 5,
                'drawdown_limit': 0.05
            },
            'database': {
                'type': 'sqlite',
                'url': 'sqlite:///smart_bot.db'
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/smart_bot.log'
            }
        }
    
    def _override_with_env_vars(self) -> None:
        """Override config values with environment variables"""
        # API Keys
        api_keys = {
            'BINANCE_API_KEY': ['apis', 'binance', 'api_key'],
            'BINANCE_SECRET_KEY': ['apis', 'binance', 'secret_key'],
            'ALPHA_VANTAGE_API_KEY': ['apis', 'alpha_vantage', 'api_key'],
            'COINGECKO_API_KEY': ['apis', 'coingecko', 'api_key'],
            'TELEGRAM_BOT_TOKEN': ['notifications', 'telegram', 'bot_token'],
            'TELEGRAM_CHAT_ID': ['notifications', 'telegram', 'chat_id'],
            'DISCORD_WEBHOOK_URL': ['notifications', 'discord', 'webhook_url']
        }
        
        for env_var, config_path in api_keys.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_value(config_path, value)
    
    def _set_nested_value(self, path: List[str], value: Any) -> None:
        """Set a nested configuration value"""
        current = self._config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('trading.daily_profit_target')
        """
        keys = path.split('.')
        current = self._config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, path: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        """
        keys = path.split('.')
        current = self._config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading-specific configuration"""
        return self.get('trading', {})
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get risk management configuration"""
        return self.get('risk', {})
    
    def get_api_config(self, api_name: str) -> Dict[str, Any]:
        """Get API configuration for specific service"""
        return self.get(f'apis.{api_name}', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.get('database', {})
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration"""
        return self.get('notifications', {})
    
    def is_production_mode(self) -> bool:
        """Check if running in production mode"""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'production'
    
    def get_log_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        log_config = self.get('logging', {})
        
        # Ensure log directory exists
        log_file = log_config.get('file', 'logs/smart_bot.log')
        log_dir = Path(log_file).parent
        log_dir.mkdir(exist_ok=True)
        
        return log_config
    
    def validate_config(self) -> List[str]:
        """
        Validate configuration and return list of issues
        """
        issues = []
        
        # Check required trading settings
        trading = self.get_trading_config()
        if not trading.get('initial_capital'):
            issues.append("Missing initial_capital in trading config")
        
        if trading.get('daily_profit_target', 0) <= 0:
            issues.append("daily_profit_target must be positive")
        
        # Check risk settings
        risk = self.get_risk_config()
        if risk.get('max_daily_loss', 0) <= 0:
            issues.append("max_daily_loss must be positive")
        
        # Check API keys if not in test mode
        if self.is_production_mode():
            if not os.getenv('BINANCE_API_KEY'):
                issues.append("BINANCE_API_KEY environment variable required for production")
        
        return issues
    
    def save_config(self, file_path: Optional[str] = None) -> bool:
        """Save current configuration to file"""
        try:
            path = file_path or self.config_path
            with open(path, 'w', encoding='utf-8') as file:
                yaml.dump(self._config, file, default_flow_style=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def reload(self) -> None:
        """Reload configuration from file"""
        self.load_config()
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary"""
        return self._config.copy()