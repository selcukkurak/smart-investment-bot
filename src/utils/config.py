"""
Configuration Manager - Konfigürasyon yönetimi
YAML, environment variables ve database konfigürasyonu
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from dotenv import load_dotenv


class ConfigManager:
    """
    Konfigürasyon yönetim sınıfı
    
    Özellikler:
    - YAML dosya desteği
    - Environment variables
    - Default değerler
    - Runtime güncelleme
    - Validation
    """
    
    def __init__(self, config_path: str = None):
        """
        Config manager başlatma
        
        Args:
            config_path: Konfigürasyon dosyası yolu
        """
        self.config_path = config_path or "config/config.yaml"
        self.config_data = {}
        self.logger = logging.getLogger('ConfigManager')
        
        # Load environment variables
        load_dotenv()
        
        # Default configuration
        self.default_config = {
            'bot': {
                'initial_capital': 10000.0,
                'trading_mode': 'paper',
                'max_positions': 10,
                'max_risk_per_trade': 0.02,
                'max_portfolio_risk': 0.10
            },
            'strategies': {
                'scalping': {
                    'enabled': True,
                    'timeframe': '5m',
                    'rsi_oversold': 30,
                    'rsi_overbought': 70,
                    'stop_loss_pct': 0.005,
                    'take_profit_pct': 0.010
                },
                'swing': {
                    'enabled': True,
                    'timeframe': '4h',
                    'rsi_oversold': 35,
                    'rsi_overbought': 65,
                    'stop_loss_pct': 0.03,
                    'take_profit_pct': 0.08
                }
            },
            'apis': {
                'binance': {
                    'testnet': True,
                    'rate_limit_per_minute': 1200
                },
                'yahoo_finance': {
                    'rate_limit_per_minute': 120
                },
                'alpha_vantage': {
                    'rate_limit_per_minute': 5
                }
            },
            'database': {
                'url': 'sqlite+aiosqlite:///smart_investment_bot.db',
                'echo': False
            },
            'web': {
                'host': '0.0.0.0',
                'port': 8000,
                'reload': False
            },
            'notifications': {
                'telegram': {
                    'enabled': False,
                    'chat_id': None
                },
                'discord': {
                    'enabled': False,
                    'webhook_url': None
                }
            },
            'risk_management': {
                'max_drawdown': 0.20,
                'stop_loss_enabled': True,
                'take_profit_enabled': True,
                'correlation_limit': 0.30
            },
            'logging': {
                'level': 'INFO',
                'file_path': 'logs/bot.log',
                'max_file_size': '10MB',
                'backup_count': 5
            }
        }
        
    async def load_config(self) -> bool:
        """
        Konfigürasyonu yükleme
        
        Returns:
            Yükleme başarılı mı
        """
        try:
            # Start with defaults
            self.config_data = self.default_config.copy()
            
            # Load from YAML file if exists
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    yaml_config = yaml.safe_load(file)
                    if yaml_config:
                        self._merge_config(self.config_data, yaml_config)
                        self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.warning(f"Config file not found: {self.config_path}, using defaults")
            
            # Override with environment variables
            self._load_env_overrides()
            
            # Validate configuration
            validation_result = self._validate_config()
            if not validation_result['valid']:
                self.logger.error(f"Configuration validation failed: {validation_result['errors']}")
                return False
            
            self.logger.info("✅ Configuration loaded and validated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error loading configuration: {str(e)}")
            return False
    
    def _merge_config(self, base: Dict, override: Dict) -> None:
        """Konfigürasyon merge etme"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _load_env_overrides(self) -> None:
        """Environment variable override'ları yükleme"""
        env_mappings = {
            # Bot settings
            'BOT_INITIAL_CAPITAL': ('bot', 'initial_capital', float),
            'BOT_TRADING_MODE': ('bot', 'trading_mode', str),
            'BOT_MAX_POSITIONS': ('bot', 'max_positions', int),
            
            # API keys
            'BINANCE_API_KEY': ('apis', 'binance', 'api_key', str),
            'BINANCE_API_SECRET': ('apis', 'binance', 'api_secret', str),
            'ALPHA_VANTAGE_API_KEY': ('apis', 'alpha_vantage', 'api_key', str),
            
            # Database
            'DATABASE_URL': ('database', 'url', str),
            
            # Web
            'WEB_HOST': ('web', 'host', str),
            'WEB_PORT': ('web', 'port', int),
            
            # Notifications
            'TELEGRAM_BOT_TOKEN': ('notifications', 'telegram', 'bot_token', str),
            'TELEGRAM_CHAT_ID': ('notifications', 'telegram', 'chat_id', str),
            'DISCORD_WEBHOOK_URL': ('notifications', 'discord', 'webhook_url', str),
        }
        
        for env_key, (section, key, value_type, *subsection) in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value:
                try:
                    # Convert type
                    if value_type == int:
                        converted_value = int(env_value)
                    elif value_type == float:
                        converted_value = float(env_value)
                    elif value_type == bool:
                        converted_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        converted_value = env_value
                    
                    # Set in config
                    if subsection:
                        # Nested key
                        if section not in self.config_data:
                            self.config_data[section] = {}
                        if subsection[0] not in self.config_data[section]:
                            self.config_data[section][subsection[0]] = {}
                        self.config_data[section][subsection[0]][key] = converted_value
                    else:
                        # Direct key
                        if section not in self.config_data:
                            self.config_data[section] = {}
                        self.config_data[section][key] = converted_value
                    
                    self.logger.debug(f"Environment override: {env_key} -> {section}.{key}")
                    
                except ValueError as e:
                    self.logger.warning(f"Invalid environment value for {env_key}: {env_value}")
    
    def _validate_config(self) -> Dict:
        """Konfigürasyon validasyonu"""
        errors = []
        
        # Required sections
        required_sections = ['bot', 'apis', 'database', 'web']
        for section in required_sections:
            if section not in self.config_data:
                errors.append(f"Missing required section: {section}")
        
        # Bot validation
        bot_config = self.config_data.get('bot', {})
        if bot_config.get('initial_capital', 0) <= 0:
            errors.append("Initial capital must be positive")
        
        if bot_config.get('max_risk_per_trade', 0) > 0.20:
            errors.append("Max risk per trade cannot exceed 20%")
        
        # Database validation
        db_config = self.config_data.get('database', {})
        if not db_config.get('url'):
            errors.append("Database URL is required")
        
        # Web validation
        web_config = self.config_data.get('web', {})
        port = web_config.get('port', 8000)
        if not (1024 <= port <= 65535):
            errors.append("Web port must be between 1024-65535")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Konfigürasyon değeri alma
        
        Args:
            key_path: Nokta ile ayrılmış key path (örn: 'bot.initial_capital')
            default: Varsayılan değer
            
        Returns:
            Konfigürasyon değeri
        """
        keys = key_path.split('.')
        current = self.config_data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Konfigürasyon değeri ayarlama
        
        Args:
            key_path: Nokta ile ayrılmış key path
            value: Yeni değer
            
        Returns:
            Ayarlama başarılı mı
        """
        keys = key_path.split('.')
        current = self.config_data
        
        try:
            # Navigate to parent
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set value
            current[keys[-1]] = value
            self.logger.info(f"Configuration updated: {key_path} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting config value: {str(e)}")
            return False
    
    async def save_config(self) -> bool:
        """
        Konfigürasyonu dosyaya kaydetme
        
        Returns:
            Kaydetme başarılı mı
        """
        try:
            # Create config directory if not exists
            config_dir = os.path.dirname(self.config_path)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            # Save to YAML
            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.config_data, file, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def get_api_credentials(self, api_name: str) -> Dict:
        """
        API credentials alma
        
        Args:
            api_name: API adı (binance, alpha_vantage, etc.)
            
        Returns:
            API credentials
        """
        api_config = self.get(f'apis.{api_name}', {})
        
        # Environment variable'lardan da kontrol et
        if api_name == 'binance':
            api_key = os.getenv('BINANCE_API_KEY') or api_config.get('api_key')
            api_secret = os.getenv('BINANCE_API_SECRET') or api_config.get('api_secret')
            
            return {
                'api_key': api_key,
                'api_secret': api_secret,
                'testnet': api_config.get('testnet', True)
            }
            
        elif api_name == 'alpha_vantage':
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY') or api_config.get('api_key')
            
            return {
                'api_key': api_key
            }
        
        return api_config
    
    def get_notification_config(self, service: str) -> Dict:
        """
        Bildirim servisi konfigürasyonu
        
        Args:
            service: Servis adı (telegram, discord)
            
        Returns:
            Bildirim konfigürasyonu
        """
        notification_config = self.get(f'notifications.{service}', {})
        
        if service == 'telegram':
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or notification_config.get('bot_token')
            chat_id = os.getenv('TELEGRAM_CHAT_ID') or notification_config.get('chat_id')
            
            return {
                'enabled': notification_config.get('enabled', False),
                'bot_token': bot_token,
                'chat_id': chat_id
            }
            
        elif service == 'discord':
            webhook_url = os.getenv('DISCORD_WEBHOOK_URL') or notification_config.get('webhook_url')
            
            return {
                'enabled': notification_config.get('enabled', False),
                'webhook_url': webhook_url
            }
        
        return notification_config
    
    def get_strategy_config(self, strategy_name: str) -> Dict:
        """
        Strateji konfigürasyonu
        
        Args:
            strategy_name: Strateji adı
            
        Returns:
            Strateji konfigürasyonu
        """
        return self.get(f'strategies.{strategy_name}', {})
    
    def update_strategy_config(self, strategy_name: str, config: Dict) -> bool:
        """
        Strateji konfigürasyonu güncelleme
        
        Args:
            strategy_name: Strateji adı
            config: Yeni konfigürasyon
            
        Returns:
            Güncelleme başarılı mı
        """
        current_config = self.get_strategy_config(strategy_name)
        current_config.update(config)
        
        return self.set(f'strategies.{strategy_name}', current_config)
    
    def get_risk_config(self) -> Dict:
        """Risk yönetimi konfigürasyonu"""
        return self.get('risk_management', {
            'max_drawdown': 0.20,
            'stop_loss_enabled': True,
            'take_profit_enabled': True,
            'max_correlation_exposure': 0.30
        })
    
    def create_example_config(self) -> bool:
        """
        Örnek konfigürasyon dosyası oluşturma
        
        Returns:
            Oluşturma başarılı mı
        """
        try:
            example_path = self.config_path.replace('.yaml', '.example.yaml')
            
            # Create directory if not exists
            os.makedirs(os.path.dirname(example_path), exist_ok=True)
            
            # Example config with placeholders
            example_config = self.default_config.copy()
            
            # Add API key placeholders
            example_config['apis']['binance'].update({
                'api_key': 'YOUR_BINANCE_API_KEY',
                'api_secret': 'YOUR_BINANCE_API_SECRET'
            })
            
            example_config['apis']['alpha_vantage'].update({
                'api_key': 'YOUR_ALPHA_VANTAGE_API_KEY'
            })
            
            example_config['notifications']['telegram'].update({
                'bot_token': 'YOUR_TELEGRAM_BOT_TOKEN',
                'chat_id': 'YOUR_TELEGRAM_CHAT_ID'
            })
            
            example_config['notifications']['discord'].update({
                'webhook_url': 'YOUR_DISCORD_WEBHOOK_URL'
            })
            
            # Save example config
            with open(example_path, 'w', encoding='utf-8') as file:
                yaml.dump(example_config, file, default_flow_style=False, indent=2)
            
            self.logger.info(f"Example configuration created: {example_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating example config: {str(e)}")
            return False
    
    def validate_api_credentials(self) -> Dict[str, bool]:
        """
        API credentials doğrulama
        
        Returns:
            Doğrulama sonuçları
        """
        results = {}
        
        # Binance credentials
        binance_creds = self.get_api_credentials('binance')
        results['binance'] = bool(
            binance_creds.get('api_key') and 
            binance_creds.get('api_secret')
        )
        
        # Alpha Vantage credentials
        alpha_vantage_creds = self.get_api_credentials('alpha_vantage')
        results['alpha_vantage'] = bool(alpha_vantage_creds.get('api_key'))
        
        # Yahoo Finance (no credentials needed)
        results['yahoo_finance'] = True
        
        return results
    
    def get_trading_pairs_config(self) -> List[Dict]:
        """Trading çiftleri konfigürasyonu"""
        return self.get('trading_pairs', [
            {
                'symbol': 'BTC/USDT',
                'asset_type': 'crypto',
                'enabled': True,
                'max_position_size': 0.10,
                'strategies': ['scalping', 'swing']
            },
            {
                'symbol': 'ETH/USDT',
                'asset_type': 'crypto',
                'enabled': True,
                'max_position_size': 0.10,
                'strategies': ['scalping', 'swing']
            },
            {
                'symbol': 'AAPL',
                'asset_type': 'stock',
                'enabled': True,
                'max_position_size': 0.08,
                'strategies': ['swing']
            },
            {
                'symbol': 'EURUSD',
                'asset_type': 'forex',
                'enabled': True,
                'max_position_size': 0.05,
                'strategies': ['swing']
            }
        ])
    
    def get_all_config(self) -> Dict:
        """Tüm konfigürasyonu alma"""
        return self.config_data.copy()
    
    def export_config_template(self, output_path: str) -> bool:
        """
        Konfigürasyon template export etme
        
        Args:
            output_path: Output dosya yolu
            
        Returns:
            Export başarılı mı
        """
        try:
            template = {
                '# Smart Investment Bot Configuration': None,
                '# Copy this file to config.yaml and update with your settings': None,
                **self.default_config
            }
            
            with open(output_path, 'w', encoding='utf-8') as file:
                yaml.dump(template, file, default_flow_style=False, indent=2)
            
            self.logger.info(f"Configuration template exported to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting config template: {str(e)}")
            return False